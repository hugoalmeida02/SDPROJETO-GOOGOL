import argparse
import grpc
from google.protobuf import empty_pb2
from concurrent import futures
from ..index_pb2 import index_pb2, index_pb2_grpc
import random
import time
import threading
import json
import os
from fastapi import WebSocket
import asyncio

MAX_INDEX_BARRELS = 3 #Número máximo de barrels
CHECK_INTERVAL = 5  # Intervalo para verificar replicas ativas
FAILURE_THRESHOLD = 3 #Número máximo de vezes que um barrel pode falhar
SAVE_INTERVAL = 5 # Intervalo para auto save à data

clients: list[WebSocket] = []

class GatewayServicer(index_pb2_grpc.IndexServicer):
    def __init__(self, host, port, host_url_queue, port_url_queue):
        self.host = host #Host gateway
        self.port = port #Port gateway
        self.url_queue = f"{host_url_queue}:{port_url_queue}"
        self.gateway_file = f"app/googol_grcp/files/gateway_data_{self.host}_{self.port}.json" #Ficheiro para guardar data da gateway
        self.search_counter = {} #Data para estatitiscas
        self.response_times = {} #Data para estatitiscas
        self.index_sizes = {} #Data para estatitiscas
        self.load_data()
        self.lock = threading.Lock()
        
        threading.Thread(target=self.auto_save, daemon=True).start() # Thread para guarda a data periodicamente
        threading.Thread(target=self.check_index_servers, daemon=True).start() # Thread para manter a informacao sobre os barrels ativos
        threading.Thread(target=self.update_stats_loop, daemon=True).start()
        
    def load_data(self):
        """Carrega os dados do ficheiro JSON ou cria ficheiro vazio se não existir."""
        if os.path.exists(self.gateway_file):
            with open(self.gateway_file, "r") as f:
                data = json.load(f)
                self.search_counter = data.get("search_counter", {})
                self.response_times = data.get("response_times", {})
                self.index_sizes = data.get("index_sizes", {})
                self.index_barrels = data.get("index_barrels", {})
            print(f"Dados carregados do ficheiro {self.gateway_file}")
        else:
            with open(self.gateway_file, "w") as f:
                json.dump({}, f)
            print(
                f"Ficheiro {self.gateway_file} não encontrado. Criado um novo ficheiro vazio.")
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
                    else:
                        self.index_barrels[address]["failures"] += 1
                        if self.index_barrels[address]["failures"] >= FAILURE_THRESHOLD:
                            to_remove.append(address)

                for address in to_remove:
                    print(f"Removido Index Server inativo: {address}")
                    del self.index_barrels[address]
            
    def update_stats_loop(self):
        last_sent_sizes = {}
        while True:
            time.sleep(5)
            updated = False
            stats_to_send = {
                "type": "stats",
                "top_queries": sorted(self.search_counter.items(), key=lambda x: x[1], reverse=True)[:10],
                "barrels": []
            }
            for address in self.index_barrels:
                try:
                    with grpc.insecure_channel(address) as channel:
                        stub = index_pb2_grpc.IndexStub(channel)
                        index_response = stub.getIndexlen(empty_pb2.Empty())
                        current_sizes = {
                            "words": index_response.lenIndexWords,
                            "urls": index_response.lenIndexUrls
                        }
                        if address not in last_sent_sizes or last_sent_sizes[address] != current_sizes:
                            updated = True
                            last_sent_sizes[address] = current_sizes
                        tempos = self.response_times.get(address, [])
                        stats_to_send["barrels"].append({
                            "address": address,
                            "index_size_words": current_sizes["words"],
                            "index_size_urls": current_sizes["urls"],
                            "avg_response_time": round(sum(tempos) / len(tempos), 3) if tempos else 0.0
                        })
                except grpc.RpcError:
                    continue
            if updated:
                asyncio.run(self.notify_clients(stats_to_send))

    async def notify_clients(self, data):
        msg = json.dumps(data)
        for ws in clients:
            try:
                await ws.send_text(msg)
            except:
                continue
                    
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
                print(f"Falha ao contactar {server}, tentando próximo...")
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
                print(f"Falha ao contactar {server}, tentando próximo...")
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
                index_response = stub.getIndexlen(empty_pb2.Empty())
                if address not in self.index_sizes:
                    self.index_sizes[address] = {}
                self.index_sizes[address]["words"] = index_response.lenIndexWords
                self.index_sizes[address]["urls"] = index_response.lenIndexUrls
                
            barrel.index_size_words = self.index_sizes.get(address, {}).get("words", 0)
            barrel.index_size_urls = self.index_sizes.get(address, {}).get("urls", 0)
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
    
    run(args.host_gateway, args.port_gateway, args.host_url_queue, args.port_url_queue)
