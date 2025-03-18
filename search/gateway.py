import grpc
import index_pb2
from google.protobuf import empty_pb2
import index_pb2_grpc
from concurrent import futures
import random

SERVERS = []
max_indexBarrels = 3

class GatewayServicer(index_pb2_grpc.IndexServicer):
    def __init__(self):
        pass

    def registerIndexBarrel(self, request, context):
        if len(SERVERS) >= max_indexBarrels:
            return index_pb2.ValidRegister(valid=False)
        else:
            if request.ip not in SERVERS:
                SERVERS.append(request.ip)
            return index_pb2.ValidRegister(valid=True)
        
       
    def getIndexBarrels(self, request, context):
        return index_pb2.IndexBarrelInfo(indexInfos=SERVERS)

    def searchWord(self, request, context):
        """Pesquisa a palavra em todos os servidores e agrega os resultados"""
        results = set()

        server_index = random.randint(0, len(SERVERS) - 1)

        while True:
            server = SERVERS[server_index]
            next_servers = SERVERS.copy()
            try:
                with grpc.insecure_channel(server) as channel:
                    stub = index_pb2_grpc.IndexStub(channel)
                    response = stub.searchWord(request)
                    print(response)
                    results.update(response.urls)
                    
                    break
            except grpc.RpcError as e:
                next_servers.remove(server)
                server_index = (server_index + 1) % len(next_servers)
                continue

        return index_pb2.SearchWordResponse(urls=list(results))

    def putNew(self, request, context):
        url_queue = "localhost:8180"
        channel = grpc.insecure_channel(url_queue)
        try:
            stub = index_pb2_grpc.IndexStub(channel)
            response = stub.putNew(request)
        except grpc.RpcError as e:
            print(f"RPC failed: {e.code()}")
            print(f"RPC error details: {e.details()}")
            
        return empty_pb2.Empty()

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
