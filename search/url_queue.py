import index_pb2
import index_pb2_grpc
import grpc
from google.protobuf import empty_pb2
from concurrent import futures
import argparse
import json
import os
import threading
import time

SAVE_INTERVAL = 5

class QueueService(index_pb2_grpc.IndexServicer):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.url_queue_file = f"url_queue_{self.host}_{self.port}.json"
        self.queue = []
        self.lock = threading.Lock()
        self.load_data()
        self.auto_save_thread = threading.Thread(target=self.auto_save, daemon=True).start()

    def load_data(self):
        """Carrega os dados do ficheiro JSON ou cria ficheiro vazio se não existir."""
        # Carregar dados do ficheiro de index, ou criar se não existir
        if os.path.exists(self.url_queue_file):
            with open(self.url_queue_file, "r") as f:
                self.queue = json.load(f)
            print(f"✅ Dados carregados do ficheiro {self.url_queue_file}")
        else:
            # Se o ficheiro não existir, cria um ficheiro vazio
            with open(self.url_queue_file, "w") as f:
                json.dump({}, f)
            print(
                f"⚠️ Ficheiro {self.url_queue_file} não encontrado. Criado um novo ficheiro vazio.")
            self.queue = []
    
    def save_data(self):
        """Guarda os dados no ficheiro JSON."""
        with self.lock:
            with open(self.url_queue_file, "w") as f:
                json.dump(self.queue, f, indent=2)

    def auto_save(self):
        """Guarda periodicamente os dados em ficheiros JSON."""
        while True:
            time.sleep(SAVE_INTERVAL)
            self.save_data()
    
    def takeNext(self, request, context):
        with self.lock:
            if self.queue:
                url = self.queue.pop(0)
                return index_pb2.TakeNextResponse(url=url)
            else:
                return index_pb2.TakeNextResponse(url="")

    def putNew(self, request, context):
        with self.lock:
            self.queue.append(request.url)
            print(f"Added URL to index: {request.url}")
        return empty_pb2.Empty()


def run(host, port):
    try:
        queue = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        queue_service = QueueService(host, port)
        index_pb2_grpc.add_IndexServicer_to_server(queue_service, queue)

        queue.add_insecure_port(f"{host}:{port}")  # O Gateway escuta na porta 8190
        queue.start()
        print(f"Queue RPC started on {host}:{port}")
        queue.wait_for_termination()
    except KeyboardInterrupt:
        print("\nStopping the Url Queue...")
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Url Queue")
    parser.add_argument("--host", type=str, required=True,
                        help="Host para o servidor gRPC")
    parser.add_argument("--port", type=str, required=True,
                        help="Porta para o servidor gRPC")
    
    args = parser.parse_args()
    
    run(args.host, args.port)
