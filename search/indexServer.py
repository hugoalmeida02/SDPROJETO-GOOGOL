from concurrent import futures
import grpc
import index_pb2
import index_pb2_grpc
from google.protobuf import empty_pb2
import threading
import argparse
import queue
import os
import json
import time

SAVE_INTERVAL = 5
CHECK_REPLICAS_INTERVAL = 5
REPLICAS = []


class IndexServicer(index_pb2_grpc.IndexServicer):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.lock = threading.Lock()
        self.pending_updates = queue.Queue()
        self.index_file_word = f"words_data_{port}.json"
        self.index_file_urls = f"urls_data_{port}.json"
        self.load_data()
        self.pending_updates = queue.Queue()

        threading.Thread(target=self.auto_save, daemon=True).start()
        threading.Thread(target=self.process_pending_updates,
                         daemon=True).start()
        threading.Thread(
            target=self.check_replicas_periodically, daemon=True).start()

    def registerIndex(self):
        gateway_channel = grpc.insecure_channel("localhost:8190")
        self.gateway_stub = index_pb2_grpc.IndexStub(gateway_channel)
        try:
            response = self.gateway_stub.registerIndexBarrel(
                index_pb2.IndexBarrelRequest(host=self.host, port=self.port))
            if response.valid:
                print("Server registado com sucesso")
                return True
            else:
                print("Nao foi possivel registar server")
                return False
        except grpc.RpcError:
            print("Erro ao registar server. Gateway indisponivel")
            return False

    def load_data(self):
        """Carrega os dados do ficheiro JSON ou cria ficheiro vazio se não existir."""
        # Carregar dados do ficheiro de index, ou criar se não existir
        if os.path.exists(self.index_file_word):
            with open(self.index_file_word, "r") as f:
                self.words_data = json.load(f)
            print(f"✅ Dados carregados do ficheiro {self.index_file_word}")
        else:
            # Se o ficheiro não existir, cria um ficheiro vazio
            with open(self.index_file_word, "w") as f:
                json.dump({}, f)
            print(
                f"⚠️ Ficheiro {self.index_file_word} não encontrado. Criado um novo ficheiro vazio.")
            self.words_data = {}
         # Carregar dados do ficheiro de index, ou criar se não existir
        if os.path.exists(self.index_file_urls):
            with open(self.index_file_urls, "r") as f:
                self.urls_data = json.load(f)
            print(f"✅ Dados carregados do ficheiro {self.index_file_urls}")
        else:
            # Se o ficheiro não existir, cria um ficheiro vazio
            with open(self.index_file_urls, "w") as f:
                json.dump({}, f)
            print(
                f"⚠️ Ficheiro {self.index_file_urls} não encontrado. Criado um novo ficheiro vazio.")
            self.urls_data = {}

    def save_data(self):
        """Guarda os dados no ficheiro JSON."""
        with self.lock:
            with open(self.index_file_word, "w") as f:
                json.dump(self.words_data, f, indent=2)
            with open(self.index_file_urls, "w") as f:
                json.dump(self.urls_data, f, indent=2)

    def auto_save(self):
        """Guarda periodicamente os dados em ficheiros JSON."""
        while True:
            time.sleep(SAVE_INTERVAL)
            self.save_data()

    def sync_with_existing_replicas(self):
        """Sincroniza com outros Index Barrels quando inicia."""

        response = self.gateway_stub.getIndexBarrels(empty_pb2.Empty())

        for server in response.indexInfos:
            if server not in REPLICAS and server != f"localhost:{self.port}":
                REPLICAS.append(server)

        for replica in REPLICAS:
            if replica == f"localhost:{self.port}":
                continue
            try:
                print(f"🔄 Tentando sincronizar com {replica}...")
                with grpc.insecure_channel(replica) as channel:
                    stub = index_pb2_grpc.IndexStub(channel)
                    response = stub.getFullIndex(empty_pb2.Empty())
                    
                    with self.lock:
                        for entry in response.palavras:
                            if entry.param0 not in self.words_data:
                                self.words_data[entry.param0] = [entry.param1]
                            else:
                                if entry.param1 not in self.words_data[entry.param0]:
                                    self.words_data[entry.param0].append(entry.param1)
                        
                        for entry in response.urls:
                            if entry.param0 not in self.urls_data:
                                self.urls_data[entry.param0] = [entry.param1]
                            else:
                                if entry.param1 not in self.urls_data[entry.param0]:
                                    self.urls_data[entry.param0].append(entry.param1)

                print(f"✅ Sincronização com {replica} concluída.")
                return
            except grpc.RpcError:
                print(f"⚠️ Falha ao sincronizar com {replica}")

        print("❌ Nenhuma réplica disponível. Iniciando vazio.")

    def update_replicas_from_gateway(self):
        """Obtém a lista de réplicas da Gateway."""
        try:
            with grpc.insecure_channel("localhost:8190") as channel:
                stub = index_pb2_grpc.IndexStub(channel)
                response = stub.getIndexBarrels(empty_pb2.Empty())

                with self.lock:
                    REPLICAS = [
                        replica for replica in response.indexInfos if replica != f"localhost:{self.port}"]
        except grpc.RpcError as e:
            print(f"⚠️ Erro ao contactar a Gateway: {e.details()}")

    def check_replicas_periodically(self):
        """Verifica periodicamente a lista de réplicas na Gateway."""
        while True:
            time.sleep(CHECK_REPLICAS_INTERVAL)
            self.update_replicas_from_gateway()

    def reliable_multicast(self, param0, param1, tipo):
        """Envia a atualização para todas as réplicas."""
        def send_update(replica, tipo):
            print(tipo, replica)
            if replica == f"{self.host}:{self.port}":
                return  # Ignorar a própria réplica
            try:
                with grpc.insecure_channel(replica) as channel:
                    stub = index_pb2_grpc.IndexStub(channel)
                    if tipo == "words":
                        stub.addToIndexWords(index_pb2.AddToIndexRequestWord(
                            word=param0, url=param1, from_multicast=True))
                    if tipo == "urls":
                        stub.addToIndexLinks(index_pb2.AddToIndexRequestLinks(
                            url=param0, link=param1, from_multicast=True))
            except grpc.RpcError:
                print(
                    f"⚠️ Falha ao replicar para {replica}. Guardando para retry.")
                self.pending_updates.put(
                    (param0, param1, tipo, replica))  # Adiciona à fila

        # Criar threads para enviar atualizações em paralelo
        threads = [threading.Thread(target=send_update, args=(
            replica, tipo,))for replica in REPLICAS]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()  # Esperar todas as threads terminarem

    def process_pending_updates(self):
        """Reenvia mensagens falhadas periodicamente."""
        while True:
            time.sleep(5)  # Tentar reenviar a cada 5 segundos
            while not self.pending_updates.empty():
                param0, param1, tipo, replica = self.pending_updates.get()
                print(
                    f"🔄 Reenviando atualização para {replica}: {param0} -> {param1}")
                try:
                    with grpc.insecure_channel(replica) as channel:
                        stub = index_pb2_grpc.IndexStub(channel)
                        if tipo == "words":
                            stub.addToIndexWords(index_pb2.AddToIndexRequestWord(
                                word=param0, url=param1, from_multicast=True))
                        if tipo == "urls":
                            stub.addToIndexLinks(index_pb2.AddToIndexRequestLinks(
                                url=param0, link=param1, from_multicast=True))
                except grpc.RpcError:
                    print(
                        f"⚠️ Falha ao reenviar para {replica}. Guardando novamente.")
                    self.pending_updates.put(
                        (param0, param1, tipo, replica))  # Reinsere na fila

    def addToIndexWords(self, request, context):
        with self.lock:
            if request.word not in self.words_data:
                self.words_data[request.word] = [request.url]
            else:
                if request.url not in self.words_data[request.word]:
                    self.words_data[request.word].append(request.url)

        if not request.from_multicast:
            threading.Thread(target=self.reliable_multicast, args=(
                request.word, request.url, "words"), daemon=True).start()
        return empty_pb2.Empty()

    def addToIndexLinks(self, request, context):
        with self.lock:
            if request.url not in self.urls_data:
                self.urls_data[request.url] = [request.link]
            else:
                if request.link not in self.urls_data[request.url]:
                    self.urls_data[request.url].append(request.link)

        if not request.from_multicast:
            threading.Thread(target=self.reliable_multicast, args=(
                request.url, request.link, "urls"), daemon=True).start()
        return empty_pb2.Empty()

    def searchWord(self, request, context):
        if " " in request.words:
            words = request.words.split(" ")
        words = request.words
        
        with self.lock:
            for word in words:
                
                
        # return index_pb2.SearchWordResponse(urls=[url[0] for url in urls])

        return index_pb2.SearchWordResponse(urls="aaaaaaa")

    def getFullIndex(self, request, context):
        """Envia todo o índice para um novo servidor que está a sincronizar."""
        with self.lock:
            entries_palavras = []
            entries_urls = []
            for palavra, urls in self.words_data.items():
                for url in urls:
                    entry = index_pb2.IndexEntry(param0=palavra, param1=url)
                    entries_palavras.append(entry)
            for url, links in self.urls_data.items():
                for link in links:
                    entry = index_pb2.IndexEntry(param0=url, param1=link)
                    entries_urls.append(entry)
                    
        return index_pb2.FullIndexResponse(palavras=entries_palavras, urls=entries_urls)


def serve(host, port):
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        index_service = IndexServicer(host, port)
        if index_service.registerIndex():
            index_service.sync_with_existing_replicas()
            index_pb2_grpc.add_IndexServicer_to_server(index_service, server)
            server.add_insecure_port(f"{host}:{port}")
            server.start()
            print(f"Server started on port {port}")

            server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nStopping the Index Barrel...")
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index Barrel")
    parser.add_argument("--host", type=str, required=True,
                        help="Host para o servidor gRPC")
    parser.add_argument("--port", type=str, required=True,
                        help="Porta para o servidor gRPC")
    # parser.add_argument("--host_gateway", type=str, required=True,
    #                     help="Host para o servidor gRPC")
    # parser.add_argument("--port_gateway", type=str, required=True,
    #                     help="Porta para o servidor gRPC")
    args = parser.parse_args()

    serve(args.host, args.port)
