from concurrent import futures
import grpc
import index_pb2
import index_pb2_grpc
from google.protobuf import empty_pb2
import threading
import time
import psutil  # Para obter estatísticas de memória
import json
import sys
import argparse
from gateway import url_queue

SAVE_INTERVAL = 10 
REPLICAS = ["localhost:8183", "localhost:8184"]

class IndexServicer(index_pb2_grpc.IndexServicer):
    def __init__(self, port):
        self.port = port
        self.index_file = f"index_data_{port}.json"
        self.indexedItems = {}
        self.lock = threading.Lock()
        self.pending_updates = []  # Lista de updates pendentes (para reenvio)
        
        self.load_index()  # Carregar índice persistido

        # Thread separada para salvar periodicamente
        self.save_thread = threading.Thread(target=self.auto_save, daemon=True)
        self.save_thread.start()
    
    def save_index(self):
        with self.lock:
            with open(self.index_file, "w") as f:
                json.dump({k: list(v) for k, v in self.indexedItems.items()}, f)
    
    def auto_save(self):
        """Thread separada que salva o índice periodicamente"""
        while True:
            time.sleep(SAVE_INTERVAL)
            self.save_index()
    
    def load_index(self):
        try:
            with open(self.index_file, "r") as f:
                data = json.load(f)
                self.indexedItems = {k: set(v) for k, v in data.items()}
            print("Índice carregado do disco.")
        except FileNotFoundError:
            print("Nenhum índice salvo encontrado. Criando novo índice.")
        except Exception as e:
            print(f"Erro ao carregar índice: {e}")
        
    def multicast_update(self, word, url):
        """Envia a atualização para todas as réplicas"""
        for replica in REPLICAS:
            if replica == f"localhost:{self.port}":
                continue  # Ignorar a própria réplica

            try:
                with grpc.insecure_channel(replica) as channel:
                    stub = index_pb2_grpc.IndexStub(channel)
                    stub.addToIndex(index_pb2.AddToIndexRequest(word=word, url=url))
            except grpc.RpcError:
                self.pending_updates.append((word, url))
    
    def retry_pending_updates(self):
        """Reenvia updates falhados periodicamente"""
        while True:
            time.sleep(5)  # Tentar reenviar a cada 5 segundos
            for word, url in list(self.pending_updates):  # Copia para evitar modificações durante o loop
                self.multicast_update(word, url)
                self.pending_updates.remove((word, url))  # Remove da lista se bem-sucedido
    
    def addToIndex(self, request, context):
        with self.lock:
            if request.word not in self.indexedItems:
                self.indexedItems[request.word] = set() 
            self.indexedItems[request.word].add(request.url)
        
        # self.multicast_update(request.word, request.url) 
        print("ADICIONADA COM SUCESSO")   
        return empty_pb2.Empty()

    def searchWord(self, request, context):
        with self.lock:
            if request.word not in self.indexedItems:
                urls = []
            else:
                urls = list(self.indexedItems[request.word])
            
        return index_pb2.SearchWordResponse(urls=urls)


def serve(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    index_service = IndexServicer(port)
    index_pb2_grpc.add_IndexServicer_to_server(index_service, server)
    
    threading.Thread(target=index_service.retry_pending_updates, daemon=True).start()  # Thread para reenvio
    
    server.add_insecure_port(f"[::]:{port}") 
    server.start()
    print(f"Server started on port {port}")
    
    server.wait_for_termination()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index Server")
    parser.add_argument("--port", type=int, required=True, help="Porta para o servidor gRPC")
    args = parser.parse_args()

    serve(args.port)