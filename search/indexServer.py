from concurrent import futures
import grpc
import index_pb2
import index_pb2_grpc
from google.protobuf import empty_pb2
import queue
import threading
import time
import psutil  # Para obter estatísticas de memória
import json
import sys

INDEX_FILE = "index_data.json"
SAVE_INTERVAL = 10 

class IndexServicer(index_pb2_grpc.IndexServicer):
    def __init__(self):
        self.urlsToIndex = queue.Queue()
        self.indexedItems = {}
        self.timestamp = time.time()
        self.lock = threading.Lock()
        self.request_count = 0  # Contador de takeNext() para estatísticas
        self.save_needed = False
        
        self.load_index()  # Carregar índice persistido

        # Thread separada para salvar periodicamente
        self.save_thread = threading.Thread(target=self.auto_save, daemon=True)
        self.save_thread.start()
        
        # URL inicial (semente)
        if self.urlsToIndex.qsize() == 0:
            self.urlsToIndex.put("https://pt.wikipedia.org/wiki/Wikip%C3%A9dia:P%C3%A1gina_principal")
    
    
    def save_index(self):
        with self.lock:
            with open(INDEX_FILE, "w") as f:
                json.dump({k: list(v) for k, v in self.indexedItems.items()}, f)
            
        self.save_needed = False  # Reset flag após salvar
    
    def auto_save(self):
        """Thread separada que salva o índice periodicamente"""
        while True:
            time.sleep(SAVE_INTERVAL)
            if self.save_needed:
                self.save_index()
    
    def load_index(self):
        try:
            with open(INDEX_FILE, "r") as f:
                data = json.load(f)
                self.indexedItems = {k: set(v) for k, v in data.items()}
            print("Índice carregado do disco.")
        except FileNotFoundError:
            print("Nenhum índice salvo encontrado. Criando novo índice.")
        except Exception as e:
            print(f"Erro ao carregar índice: {e}")
        
    def putNew(self, request, context):
        self.urlsToIndex.put(request.url)
        # print(f"Added URL to index: {request.url}")
        return empty_pb2.Empty()

    def takeNext(self, request, context):
        url = self.urlsToIndex.get()
        # print(f"Providing URL to worker: {url}")
        
        # Estatísticas de desempenho
        self.request_count += 1
        current_time = time.time()
        elapsed_time = current_time - self.timestamp
        pages_per_second = 10.0 / elapsed_time if elapsed_time > 0 else 0
        object_memory = sys.getsizeof(self.indexedItems) + sys.getsizeof(self.urlsToIndex)
        print(f"Performance: {pages_per_second:.2f} pages/sec, Memory: {object_memory} bytes")
        
        self.timestamp = current_time
        
        return index_pb2.TakeNextResponse(url=url)
    
    def addToIndex(self, request, context):
        with self.lock:
            if request.word not in self.indexedItems:
                self.indexedItems[request.word] = set() 
            self.indexedItems[request.word].add(request.url)
            # print(f"Indexed word '{request.word}' for URL: {request.url}")
        self.save_needed = True
        return empty_pb2.Empty()

    def searchWord(self, request, context):
        with self.lock:
            if request.word not in self.indexedItems:
                urls = []
            else:
                urls = list(self.indexedItems[request.word])
            
        return index_pb2.SearchWordResponse(urls=urls)

    def getStats(self, request, context):
        """ Retorna estatísticas do servidor """
        with self.lock:
            total_urls = sum(len(urls) for urls in self.indexedItems.values())
            total_words = len(self.indexedItems)
            memory_usage = psutil.Process().memory_info().rss  # Memória usada pelo processo
            
        return index_pb2.StatsResponse(
            total_urls=int(total_urls),
            total_words=int(total_words),
            memory_usage=int(memory_usage),
            pages_per_second=int(10.0 / (time.time() - self.timestamp)) if self.request_count > 0 else 0
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    index_service = IndexServicer()
    index_pb2_grpc.add_IndexServicer_to_server(index_service, server)
    server_port = 8183
    server.add_insecure_port("0.0.0.0:{}".format(server_port))
    # server.add_insecure_port("[::]:{}".format(server_port))
    server.start()
    print("Server started on port {}".format(server_port))
    
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
