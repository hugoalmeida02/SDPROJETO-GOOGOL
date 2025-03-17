import index_pb2
import index_pb2_grpc
import grpc
from google.protobuf import empty_pb2
from concurrent import futures
import argparse
import queue


class QueueService(index_pb2_grpc.IndexServicer):
    def __init__(self):
        self.queue = queue.Queue()
        
    def takeNext(self, request, context):
        url = self.queue.get()
        return index_pb2.TakeNextResponse(url=url)
    
    def putNew(self, request, context):
        self.queue.put(request.url)
        print(f"Added URL to index: {request.url}")
        return empty_pb2.Empty()
    
def queue(ip):
    queue1 = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    queue_service = QueueService()
    index_pb2_grpc.add_IndexServicer_to_server(queue_service, queue1)

    queue1.add_insecure_port(ip)  # O Gateway escuta na porta 8190
    queue1.start()
    print(f"Queue RPC iniciado em {ip}")
    queue1.wait_for_termination()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index Barrel")
    parser.add_argument("--ip", type=str, required=True,
                        help="Porta para o servidor gRPC")
    args = parser.parse_args()

    queue(args.ip)
