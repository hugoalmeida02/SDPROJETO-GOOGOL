import grpc
import index_pb2
from google.protobuf import empty_pb2
import index_pb2_grpc
from concurrent import futures
import random
import time
import threading

MAX_INDEX_BARRELS = 3
CHECK_INTERVAL = 5
FAILURE_THRESHOLD = 3

class GatewayServicer(index_pb2_grpc.IndexServicer):
    def __init__(self):
        self.host = "localhost"
        self.port = "8190"
        self.url_queue = "localhost:8180"
        self.index_barrels = {}
        self.lock = threading.Lock()
        
        threading.Thread(target=self.check_index_servers, daemon=True).start()

    def registerIndexBarrel(self, request, context):
        
        address = f"{request.host}:{request.port}"
        
        if len(self.index_barrels) >= MAX_INDEX_BARRELS:
            return index_pb2.ValidRegister(valid=False)
        else:
            if address not in self.index_barrels:
                self.index_barrels[address] = {"failures": 0}
            return index_pb2.ValidRegister(valid=True)

    def getIndexBarrels(self, request, context):
        response = []
        with self.lock:
            for address in self.index_barrels:
                response.append(address)

        return index_pb2.IndexBarrelInfo(indexInfos=response)

    def ping_server(self, address):
        try:
            with grpc.insecure_channel(address) as channel:
                stub = index_pb2_grpc.IndexStub(channel)
                stub.searchWord(index_pb2.SearchWordRequest(words="ping"))
            return True
        except grpc.RpcError:
            return False
        
    def check_index_servers(self):
        while True:
            time.sleep(CHECK_INTERVAL)
            to_remove = []
            with self.lock:
                for address in list(self.index_barrels.keys()):
                    if self.ping_server(address):
                        self.index_barrels[address]["failures"] = 0
                        print(f"✅ Sucesso ao contactar {address}")
                    else:
                        self.index_barrels[address]["failures"] += 1
                        print(f"⚠️ Falha {self.index_barrels[address]['failures']} ao contactar {address}")
                        if self.index_barrels[address]["failures"] >= FAILURE_THRESHOLD:
                            to_remove.append(address)

                for address in to_remove:
                    print(f"❌ Removido Index Server inativo: {address}")
                    del self.index_barrels[address]
            
            
    def searchWord(self, request, context):
        """Pesquisa a palavra em todos os servidores e agrega os resultados"""
        
        active_servers = [barrel for barrel in self.index_barrels.keys()]
        random.shuffle(active_servers)
        results = set()
        print(request)
        for server in active_servers:
            try:
                with grpc.insecure_channel(server) as channel:
                    stub = index_pb2_grpc.IndexStub(channel)
                    response = stub.searchWord(request)
                    results.update(response.urls)
                    break
            except grpc.RpcError as e:
                print(f"⚠️ Falha ao contactar {server}, tentando próximo...")
                continue

        return index_pb2.SearchWordResponse(urls=list(results))

    def putNew(self, request, context):
        channel = grpc.insecure_channel(self.url_queue)
        try:
            stub = index_pb2_grpc.IndexStub(channel)
            stub.putNew(request)
        except grpc.RpcError as e:
            print(f"RPC failed: {e.code()}")
            print(f"RPC error details: {e.details()}")

        return empty_pb2.Empty()

def serve():
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        gateway_service = GatewayServicer()
        index_pb2_grpc.add_IndexServicer_to_server(gateway_service, server)

        server.add_insecure_port("localhost:8190")  # O Gateway escuta na porta 8190
        server.start()
        print("Gateway RPC iniciado na porta 8190...")
        server.wait_for_termination()
    except KeyboardInterrupt:
            print("\nStopping the Gateway...")
            return


if __name__ == "__main__":
    serve()
