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

SAVE_INTERVAL = 5  # Intervalo para auto save à data
CHECK_REPLICAS_INTERVAL = 5  # Intervalo para verificar replicas ativas


class IndexServicer(index_pb2_grpc.IndexServicer):
    def __init__(self, host, port, host_gateway, port_gateway):
        self.host = host  # Host do barrel
        self.port = port  # Port do barrel
        # Host e port do gateway
        self.gateway = f"{host_gateway}:{port_gateway}"
        self.lock = threading.Lock()
        # Queue guardar a data a reenviar para as replicas se o multicast falhar
        self.pending_updates = queue.Queue()
        # File para guardar as palavras e url correspondentes
        self.index_file_word = f"words_data_{self.host}_{self.port}.json"
        # File para guardar as url, title e quote de uma url especifica
        self.index_file_urls = f"urls_data_{self.host}_{self.port}.json"
        self.load_data()
        self.replicas = []  # Guarda as replicas ativas

        # Thread para guarda a data periodicamente
        threading.Thread(target=self.auto_save, daemon=True).start()
        threading.Thread(target=self.process_pending_updates,
                         # Thread para reenviar a data que falhou no multicast
                         daemon=True).start()
        threading.Thread(
            # Thread para manter a informacao sobre as replicas ativas
            target=self.check_replicas_periodically, daemon=True).start()

    def registerIndex(self):
        """ Regista o index barrel na gateway ao inicar """
        gateway_channel = grpc.insecure_channel(self.gateway)
        self.gateway_stub = index_pb2_grpc.IndexStub(gateway_channel)
        try:
            response = self.gateway_stub.registerIndexBarrel(
                index_pb2.IndexBarrelRequest(host=self.host, port=self.port))
            if response.valid:
                print("Server registado com sucesso")
                return True
            else:
                print("Não foi possivel registar server")
                return False
        except grpc.RpcError:
            print("Erro ao registar server. Gateway indisponível")
            return False

    def load_data(self):
        """Carrega os dados do ficheiro JSON ou cria ficheiro vazio se não existir."""
        if os.path.exists(self.index_file_word):
            with open(self.index_file_word, "r") as f:
                self.words_data = json.load(f)
            print(f"✅ Dados carregados do ficheiro {self.index_file_word}")
        else:
            with open(self.index_file_word, "w") as f:
                json.dump({}, f)
            print(
                f"⚠️ Ficheiro {self.index_file_word} não encontrado. Criado um novo ficheiro vazio.")
            self.words_data = {}

        if os.path.exists(self.index_file_urls):
            with open(self.index_file_urls, "r") as f:
                self.urls_data = json.load(f)
            print(f"✅ Dados carregados do ficheiro {self.index_file_urls}")
        else:
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
            if server not in self.replicas and server != f"{self.host}:{self.port}":
                self.replicas.append(server)

        for replica in self.replicas:
            if replica == f"{self.host}:{self.port}":
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
                                    self.words_data[entry.param0].append(
                                        entry.param1)

                        for entry in response.urls:
                            if entry.param0 not in self.urls_data:
                                self.urls_data[entry.param0] = [entry.param1]
                            else:
                                if entry.param1 not in self.urls_data[entry.param0]:
                                    self.urls_data[entry.param0].append(
                                        entry.param1)

                print(f"✅ Sincronização com {replica} concluída.")
                return
            except grpc.RpcError:
                print(f"⚠️ Falha ao sincronizar com {replica}")

        print("❌ Nenhuma réplica disponível. Iniciando vazio.")

    def update_replicas_from_gateway(self):
        """Obtém a lista de réplicas da Gateway."""
        try:
            with grpc.insecure_channel(self.gateway) as channel:
                stub = index_pb2_grpc.IndexStub(channel)
                response = stub.getIndexBarrels(empty_pb2.Empty())

                with self.lock:
                    self.replicas = [
                        replica for replica in response.indexInfos if replica != f"{self.host}:{self.port}"]
                    print(self.replicas)
        except grpc.RpcError as e:
            print(f"⚠️ Erro ao contactar a Gateway: {e.details()}")

    def check_replicas_periodically(self):
        """Verifica periodicamente a lista de réplicas na Gateway."""
        while True:
            time.sleep(CHECK_REPLICAS_INTERVAL)
            self.update_replicas_from_gateway()

    def reliable_multicast(self, param0, param1, param2, param3, tipo):
        """Envia a atualização para todas as réplicas."""
        def send_update(replica, tipo):
            if replica == f"{self.host}:{self.port}":
                return  # Ignorar a própria réplica
            try:
                with grpc.insecure_channel(replica) as channel:
                    stub = index_pb2_grpc.IndexStub(channel)
                    if tipo == "words":
                        stub.addToIndexWords(index_pb2.AddToIndexRequestWords(
                            word=param0, url=param1, from_multicast=True))
                    if tipo == "urls":
                        stub.addToIndexLinks(index_pb2.AddToIndexRequestLinks(
                            url=param0, title=param1, quote=param2, link=param3, from_multicast=True))
            except grpc.RpcError:
                print(
                    f"⚠️ Falha ao replicar para {replica}. Guardando para retry.")
                self.pending_updates.put(
                    (param0, param1, param2, param3, tipo, replica))

        # Criar threads para enviar atualizações em paralelo
        threads = [threading.Thread(target=send_update, args=(
            replica, tipo,))for replica in self.replicas]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    def process_pending_updates(self):
        """Reenvia mensagens falhadas periodicamente."""
        while True:
            time.sleep(5)  # Tentar reenviar a cada 5 segundos
            param0, param1, param2, param3, tipo, replica = self.pending_updates.get()
            print(
                f"🔄 Reenviando atualização para {replica}")
            try:
                with grpc.insecure_channel(replica) as channel:
                    stub = index_pb2_grpc.IndexStub(channel)
                    if tipo == "words":
                        stub.addToIndexWords(index_pb2.AddToIndexRequestWords(
                            word=param0, url=param1, from_multicast=True))
                    if tipo == "urls":
                        stub.addToIndexLinks(index_pb2.AddToIndexRequestLinks(
                            url=param0, title=param1, quote=param2, link=param3, from_multicast=True))
            except grpc.RpcError:
                print(
                    f"⚠️ Falha ao reenviar para {replica}. Guardando novamente.")
                self.pending_updates.put(
                    (param0, param1, param2, param3, tipo, replica))

    def addToIndexWords(self, request, context):
        """ Adiciona as palavras dentro de uma página à data do index """
        with self.lock:
            if request.word not in self.words_data:
                self.words_data[request.word] = [request.url]
            else:
                if request.url not in self.words_data[request.word]:
                    self.words_data[request.word].append(request.url)

        if not request.from_multicast:
            threading.Thread(target=self.reliable_multicast, args=(
                request.word, request.url, None, None, "words"), daemon=True).start()
        return empty_pb2.Empty()

    def addToIndexLinks(self, request, context):
        """ Adiciona os urls, title e quote correspondentes a uma página à data do index """
        with self.lock:
            if request.url not in self.urls_data:
                self.urls_data[request.url] = {}
                self.urls_data[request.url]["title"] = request.title
                self.urls_data[request.url]["quote"] = request.quote
                self.urls_data[request.url]["urls"] = []

            if request.link not in self.urls_data[request.url]:
                self.urls_data[request.url]["urls"].append(request.link)

        if not request.from_multicast:
            threading.Thread(target=self.reliable_multicast, args=(
                request.url, request.title, request.quote, request.link, "urls"), daemon=True).start()
        return empty_pb2.Empty()

    def searchWord(self, request, context):
        """ Procura os urls correspondentes a uma conjunto de palavras ou a uma unica palavra """
        with self.lock:
            palavras = request.words.split()

            if not palavras:
                return index_pb2.SearchWordResponse(urls=[index_pb2.WordInfo()])

            if palavras[0] in self.words_data:
                urls_comuns = set(self.words_data[palavras[0]])
            else:

                return index_pb2.SearchWordResponse(urls=[index_pb2.WordInfo()])

            for palavra in palavras[1:]:
                if palavra in self.words_data:
                    urls_comuns &= set(self.words_data[palavra])
                else:
                    return index_pb2.SearchWordResponse(urls=[index_pb2.WordInfo()])

            urls_com_importancia = []
            for url in urls_comuns:
                importancia = 0
                for urls in self.urls_data.items():
                    if url in urls[1]["urls"]:
                        importancia += 1
                urls_com_importancia.append(
                    [url, self.urls_data[url]["title"], self.urls_data[url]["quote"], importancia])

            urls_ordenados = sorted(
                urls_com_importancia, key=lambda x: x[3], reverse=True)

            urls = []
            for url, title, quote, _ in urls_ordenados:
                url_info = index_pb2.WordInfo()
                url_info.url = url
                url_info.title = title
                url_info.quote = quote
                urls.append(url_info)

        return index_pb2.SearchWordResponse(urls=urls)

    def searchBacklinks(self, request, context):
        """ Procura os backlinks de uma página """
        with self.lock:
            backlinks = []
            for urls in self.urls_data.items():
                if request.url in urls[1]["urls"]:
                    backlinks.append(urls[0])

        return index_pb2.SearchBacklinksResponse(backlinks=backlinks)

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


def run(host, port, host_gateway, port_gateway):
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        index_service = IndexServicer(host, port, host_gateway, port_gateway)
        if index_service.registerIndex():
            index_service.sync_with_existing_replicas()
            index_pb2_grpc.add_IndexServicer_to_server(index_service, server)
            server.add_insecure_port(f"{host}:{port}")
            server.start()
            print(f"Server started on {host}:{port}")

            server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nStopping the Index Barrel...")
        index_service.save_data()
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index Barrel")
    parser.add_argument("--host", type=str, required=True,
                        help="Host para o servidor gRPC")
    parser.add_argument("--port", type=str, required=True,
                        help="Porta para o servidor gRPC")
    parser.add_argument("--host_gateway", type=str, required=True,
                        help="Host para o servidor gRPC")
    parser.add_argument("--port_gateway", type=str, required=True,
                        help="Porta para o servidor gRPC")
    args = parser.parse_args()

    run(args.host, args.port, args.host_gateway, args.port_gateway)
