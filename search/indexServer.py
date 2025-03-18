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

SAVE_INTERVAL = 2
REPLICAS = []

class IndexServicer(index_pb2_grpc.IndexServicer):
    def __init__(self, port):
        self.port = port
        self.lock = threading.Lock()
        self.pending_updates = queue.Queue()
        self.index_file = f"index_data_{port}.json"
        self.load_data()
        
        threading.Thread(target=self.auto_save, daemon=True).start()
        
    def registerIndex(self):
        gateway_channel = grpc.insecure_channel("localhost:8190")
        self.gateway_stub = index_pb2_grpc.IndexStub(gateway_channel)
        try:
            response = self.gateway_stub.registerIndexBarrel(index_pb2.IndexBarrelRequest(ip=f"localhost:{self.port}"))
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
        if os.path.exists(self.index_file):
            with open(self.index_file, "r") as f:
                self.index_data = json.load(f)
            print(f"✅ Dados carregados do ficheiro {self.index_file}")
        else:
            # Se o ficheiro não existir, cria um ficheiro vazio
            with open(self.index_file, "w") as f:
                json.dump({}, f)
            print(f"⚠️ Ficheiro {self.index_file} não encontrado. Criado um novo ficheiro vazio.")
            self.index_data = {}

    def save_data(self):
        """Guarda os dados no ficheiro JSON."""
        with self.lock:
            with open(self.index_file, "w") as f:
                json.dump(self.index_data, f, indent=2)
    
    
    def auto_save(self):
        """Guarda periodicamente os dados em ficheiros JSON."""
        while True:
            time.sleep(SAVE_INTERVAL)
            self.save_data() 
            
    
    def sync_with_existing_replicas(self):
        """Sincroniza com outros Index Barrels quando inicia."""
        
        response = self.gateway_stub.getIndexBarrels(empty_pb2.Empty())
        
        for server in response.indexInfos:
            if server not in REPLICAS:
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
                        for entry in response.entries:
                            if entry.palavra not in self.index_data:
                                self.index_data[entry.palavra] = {}
                            self.index_data[entry.palavra][entry.url] = entry.frequencia
                            
                print(f"✅ Sincronização com {replica} concluída.")
                return  
            except grpc.RpcError:
                print(f"⚠️ Falha ao sincronizar com {replica}")

        print("❌ Nenhuma réplica disponível. Iniciando vazio.")
        

    # def process_pending_updates(self):
    #     while True:
    #         time.sleep(5)  # Tentar reenviar a cada 5 segundos
    #         if not self.pending_updates.empty():
    #             word, url, replica = self.pending_updates.get()
    #             self.replicate_update(word, url)  # Tenta reenviar a mensagem

    def addToIndex(self, request, context):
        """Adiciona uma palavra e URL ao índice e replica para outras réplicas."""
        with self.lock:
            if request.word not in self.index_data:
                self.index_data[request.word] = {}
            if request.url in self.index_data[request.word]:
                self.index_data[request.word][request.url] += 1
            else:
                self.index_data[request.word][request.url] = 1

        #threading.Thread(target=self.replicate_update, args=(request.word, request.url), daemon=True).start()
        return empty_pb2.Empty()


    def searchWord(self, request, context):
        """Busca URLs para uma palavra, ordenados por frequência."""
        with self.lock:
            urls = sorted(self.index_data.get(request.word, {}).items(), key=lambda x: x[1], reverse=True)
        return index_pb2.SearchWordResponse(urls=[url[0] for url in urls])

    def getFullIndex(self, request, context):
        
        """Envia todo o índice para um novo servidor que está a sincronizar."""
        with self.lock:
            entries = []
            for palavra, urls in self.index_data.items():
                for url, frequencia in urls.items(): 
                    entry = index_pb2.IndexEntry(palavra=palavra, url=url, frequencia=frequencia)
                entries.append(entry)
                    
        return index_pb2.FullIndexResponse(entries=entries)


def serve(port):
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        index_service = IndexServicer(port)
        if index_service.registerIndex():
            index_service.sync_with_existing_replicas()
            index_pb2_grpc.add_IndexServicer_to_server(index_service, server)
            server.add_insecure_port(f"[::]:{port}")
            server.start()
            print(f"Server started on port {port}")

            server.wait_for_termination()
    except KeyboardInterrupt:
            print("\nStopping the Index Barrel...")
            return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index Barrel")
    parser.add_argument("--ip", type=int, required=True,
                        help="Porta para o servidor gRPC")
    args = parser.parse_args()

    serve(args.ip)
