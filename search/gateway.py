import grpc
import index_pb2
import index_pb2_grpc
from concurrent import futures
import random
import threading

# Lista de servidores disponíveis
SERVERS = [
    "localhost:8183",
    "localhost:8184",
    "localhost:8185"
]

class GatewayServicer(index_pb2_grpc.IndexServicer):
    def __init__(self):
        self.servers = SERVERS
        self.lock = threading.Lock()

    def choose_server(self):
        """Escolhe um servidor de forma aleatória (Round-Robin pode ser implementado aqui)"""
        return random.choice(self.servers)

    def putNew(self, request, context):
        """Encaminha um pedido de novo URL para um servidor disponível"""
        server = self.choose_server()
        with grpc.insecure_channel(server) as channel:
            stub = index_pb2_grpc.IndexStub(channel)
            return stub.putNew(request)

    def addToIndex(self, request, context):
        """Encaminha a indexação de uma palavra para um servidor aleatório"""
        server = self.choose_server()
        with grpc.insecure_channel(server) as channel:
            stub = index_pb2_grpc.IndexStub(channel)
            return stub.addToIndex(request)

    def searchWord(self, request, context):
        """Pesquisa a palavra em todos os servidores e agrega os resultados"""
        results = set()
        for server in self.servers:
            with grpc.insecure_channel(server) as channel:
                stub = index_pb2_grpc.IndexStub(channel)
                response = stub.searchWord(request)
                results.update(response.urls)

        return index_pb2.SearchWordResponse(urls=list(results))

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    gateway_service = GatewayServicer()
    index_pb2_grpc.add_IndexServicer_to_server(gateway_service, server)

    server.add_insecure_port("[::]:8190")  # O Gateway escuta na porta 8190
    server.start()
    print("Gateway RPC iniciado na porta 8190...")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
