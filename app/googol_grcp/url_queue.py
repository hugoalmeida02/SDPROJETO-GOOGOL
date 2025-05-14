import grpc
from google.protobuf import empty_pb2
from concurrent import futures
import argparse
import json
import os
import threading
import time

from ..index_pb2 import index_pb2, index_pb2_grpc

SAVE_INTERVAL = 5  # Intervalo para auto save à data

class QueueService(index_pb2_grpc.IndexServicer):
    def __init__(self, host, port):
        self.host = host  # Host queue
        self.port = port  # Host port
        # Ficheiro para guardar a informação na queue
        self.url_queue_file = f"app/googol_grcp/files/url_queue_{self.host}_{self.port}.json"
        self.queue = []
        self.lock = threading.Lock()
        self.load_data()

        # Thread para guarda a data periodicamente
        threading.Thread(target=self.auto_save, daemon=True).start()

    def load_data(self):
        """ Carrega os dados do ficheiro JSON ou cria ficheiro vazio se não existir """
        if os.path.exists(self.url_queue_file):
            with open(self.url_queue_file, "r") as f:
                self.queue = json.load(f)
            print(f"Dados carregados do ficheiro {self.url_queue_file}")
        else:
            with open(self.url_queue_file, "w") as f:
                json.dump({}, f)
            print(
                f"Ficheiro {self.url_queue_file} não encontrado. Criado um novo ficheiro vazio.")
            self.queue = []

    def save_data(self):
        """ Guarda os dados no ficheiro JSON """
        with self.lock:
            with open(self.url_queue_file, "w") as f:
                json.dump(self.queue, f, indent=2)

    def auto_save(self):
        """ Guarda periodicamente os dados em ficheiros JSON """
        while True:
            time.sleep(SAVE_INTERVAL)
            self.save_data()

    def takeNext(self, request, context):
        """ Retira um url da queue """
        with self.lock:
            if self.queue:
                url = self.queue.pop(0)
                return index_pb2.TakeNextResponse(url=url)
            else:
                return index_pb2.TakeNextResponse(url="")

    def putNew(self, request, context):
        """ Coloca um novo url na queue """
        with self.lock:
            self.queue.append(request.url)
            print(f"Added URL to index: {request.url}")
        return empty_pb2.Empty()


def run(host, port):
    try:
        queue = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        queue_service = QueueService(host, port)
        index_pb2_grpc.add_IndexServicer_to_server(queue_service, queue)

        queue.add_insecure_port(f"{host}:{port}")
        queue.start()
        print(f"Queue RPC started on {host}:{port}")
        queue.wait_for_termination()
    except KeyboardInterrupt:
        print("\nStopping the Url Queue...")
        queue_service.save_data()
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Url Queue")
    parser.add_argument("--host_url_queue", type=str, required=True,
                        help="Host para a url_queue")
    parser.add_argument("--port_url_queue", type=str, required=True,
                        help="Porta para a url_queue")

    args = parser.parse_args()

    run(args.host_url_queue, args.port_url_queue)
