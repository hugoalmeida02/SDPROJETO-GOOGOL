import argparse
import grpc
import index_pb2
from google.protobuf import empty_pb2
import index_pb2_grpc
from concurrent import futures
import random
import time
import threading
import json
import os

MAX_INDEX_BARRELS = 3 #Número máximo de barrels
CHECK_INTERVAL = 5  # Intervalo para verificar replicas ativas
FAILURE_THRESHOLD = 3 #Número máximo de vezes que um barrel pode falhar
SAVE_INTERVAL = 5 # Intervalo para auto save à data

class GatewayServicer(index_pb2_grpc.IndexServicer):
    def __init__(self, host, port, host_url_queue, port_url_queue):
        self.host = host #Host gateway
        self.port = port #Port gateway
        self.url_queue = f"{host_url_queue}:{port_url_queue}"
        self.gateway_file = f"gateway_data_{self.host}_{self.port}.json" #Ficheiro para guardar data da gateway
        self.search_counter = {} #Data para estatitiscas
        self.response_times = {} #Data para estatitiscas
        self.index_sizes = {} #Data para estatitiscas
        self.load_data()
        self.lock = threading.Lock()
        
        threading.Thread(target=self.auto_save, daemon=True).start() # Thread para guarda a data periodicamente
        threading.Thread(target=self.check_index_servers, daemon=True).start() # Thread para manter a informacao sobre os barrels ativos

    def load_data(self):
        """Carrega os dados do ficheiro JSON ou cria ficheiro vazio se não existir."""
        if os.path.exists(self.gateway_file):
            with open(self.gateway_file, "r") as f:
                data = json.load(f)
                self.search_counter = data.get("search_counter", {})
                self.response_times = data.get("response_times", {})
                self.index_sizes = data.get("index_sizes", {})
                self.index_barrels = data.get("index_barrels", {})
            print(f"✅ Dados carregados do ficheiro {self.gateway_file}")
        else:
            with open(self.gateway_file, "w") as f:
                json.dump({}, f)
            print(
                f"⚠️ Ficheiro {self.gateway_file} não encontrado. Criado um novo ficheiro vazio.")
            self.search_counter = {}
            self.response_times = {}
            self.index_sizes = {}
            self.index_barrels = {}
        
    def save_data(self):
        """Guarda os dados no ficheiro JSON."""
        with self.lock:
            data = {
                "search_counter": self.search_counter,
                "response_times": self.response_times,
                "index_sizes": self.index_sizes,
                "index_barrels" : self.index_barrels
            }
            with open(self.gateway_file, "w") as f:
                json.dump(data, f, indent=2)
                
    def auto_save(self):
        """Guarda periodicamente os dados em ficheiros JSON."""
        while True:
            time.sleep(SAVE_INTERVAL)
            self.save_data()
    
    def registerIndexBarrel(self, request, context):
        """ Regista o index barrel na gateway ao inicar """
        address = f"{request.host}:{request.port}"
        
        if len(self.index_barrels) >= MAX_INDEX_BARRELS:
            return index_pb2.ValidRegister(valid=False)
        else:
            if address not in self.index_barrels:
                self.index_barrels[address] = {"failures": 0}
            return index_pb2.ValidRegister(valid=True)

    def getIndexBarrels(self, request, context):
        """ Informa acerca dos Index Barrels ativos """
        response = []
        with self.lock:
            for address in self.index_barrels:
                response.append(address)

        return index_pb2.IndexBarrelInfo(indexInfos=response)

    def ping_server(self, address):
        """ Função pingar um Index Barrel para verificar está ativo """
        try:
            with grpc.insecure_channel(address) as channel:
                stub = index_pb2_grpc.IndexStub(channel)
                stub.searchWord(index_pb2.SearchWordRequest(words="ping"))
            return True
        except grpc.RpcError:
            return False
        
    def check_index_servers(self):
        """ Função para verificar se um Barrel está ativo """
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
        termos = request.words.strip().lower()
        self.search_counter[termos] = self.search_counter.get(termos, 0) + 1
        
        active_servers = [barrel for barrel in self.index_barrels.keys()]
        random.shuffle(active_servers)
        results = []
        
        for server in active_servers:
            try:
                start = time.time()
                with grpc.insecure_channel(server) as channel:
                    stub = index_pb2_grpc.IndexStub(channel)
                    response = stub.searchWord(request)
                    results = response.urls
                duration = (time.time() - start) * 10  
                
                # Registar tempo
                if server not in self.response_times:
                    self.response_times[server] = []
                self.response_times[server].append(duration)

                break
            except grpc.RpcError as e:
                print(f"⚠️ Falha ao contactar {server}, tentando próximo...")
                continue

        return index_pb2.SearchWordResponse(urls=results)

    def searchBacklinks(self, request, context):
        """Pesquisa a palavra em todos os servidores e agrega os resultados"""
        
        active_servers = [barrel for barrel in self.index_barrels.keys()]
        random.shuffle(active_servers)
        results = []
        
        for server in active_servers:
            try:
                start = time.time()
                with grpc.insecure_channel(server) as channel:
                    stub = index_pb2_grpc.IndexStub(channel)
                    response = stub.searchBacklinks(request)
                    results = response.backlinks
                duration = (time.time() - start) * 10  
                
                # Registar tempo
                if server not in self.response_times:
                    self.response_times[server] = []
                self.response_times[server].append(duration)
                break
            
            except grpc.RpcError as e:
                print(f"⚠️ Falha ao contactar {server}, tentando próximo...")
                continue

        return index_pb2.SearchBacklinksResponse(backlinks=results)

    def putNew(self, request, context):
        """ Coloca o url fornecido pelo client na queue"""
        channel = grpc.insecure_channel(self.url_queue)
        try:
            stub = index_pb2_grpc.IndexStub(channel)
            stub.putNew(request)
        except grpc.RpcError as e:
            print(f"RPC failed: {e.code()}")
            print(f"RPC error details: {e.details()}")

        return empty_pb2.Empty()
    
    def getStats(self, request, context):
        """ Retorna as estáticas """
        response = index_pb2.SystemStats()

        # Top 10 pesquisas
        sorted_queries = sorted(self.search_counter.items(), key=lambda x: x[1], reverse=True)[:10]
        for term, _ in sorted_queries:
            response.top_queries.append(term)

        # Info de cada barrel
        for address in self.index_barrels:
            barrel = response.barrels.add()
            barrel.address = address
            
            with grpc.insecure_channel(address) as channel:
                stub = index_pb2_grpc.IndexStub(channel)
                index_response = stub.getFullIndex(empty_pb2.Empty())
                self.index_sizes[address] = len(index_response.palavras)
                
            barrel.index_size = self.index_sizes.get(address, 0)
            tempos = self.response_times.get(address, [])
            barrel.avg_response_time = round(sum(tempos) / len(tempos), 3) if tempos else 0.0

        return response

def run(host, port, host_url_queue, port_url_queue):
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        gateway_service = GatewayServicer(host, port, host_url_queue, port_url_queue)
        index_pb2_grpc.add_IndexServicer_to_server(gateway_service, server)

        server.add_insecure_port(f"{host}:{port}")
        server.start()
        print(f"Gateway RPC started on {host}:{port}")
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nStopping the Gateway...")
        gateway_service.save_data()
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gateway")
    parser.add_argument("--host_gateway", type=str, required=True,
                        help="Host para o servidor gRPC")
    parser.add_argument("--port_gateway", type=str, required=True,
                        help="Porta para o servidor gRPC")
    parser.add_argument("--host_url_queue", type=str, required=True,
                        help="Host para o servidor gRPC")
    parser.add_argument("--port_url_queue", type=str, required=True,
                        help="Porta para o servidor gRPC")
    args = parser.parse_args()
    
    run(args.host, args.port, args.host_url_queue, args.port_url_queue)
