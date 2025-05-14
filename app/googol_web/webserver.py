import grpc
from google.protobuf import empty_pb2
from concurrent import futures
import time
import asyncio
import json

from .websockets import broadcast_message
from ..index_pb2 import index_pb2, index_pb2_grpc

# WebServer gRPC para comunicação com a Gateway
class WebSever(index_pb2_grpc.IndexServicer):
    def __init__(self, host, port, host_gateway, port_gateway):
        self.host = host
        self.port = port
        self.gateway = f"{host_gateway}:{port_gateway}"
        self.gateway_stub = self.get_gateway_stub()
        self.start_sending_statistics()

    def get_gateway_stub(self):
        while True:
            try:
                channel = grpc.insecure_channel(self.gateway)
                stub = index_pb2_grpc.IndexStub(channel)
                return stub
            except:
                time.sleep(2)
                print("Tentado conectar à gatewaay")

    def put_new_url(self, url):
        """ Envia novo URL para a fila de URLs (via Gateway) """
        self.gateway_stub.putNew(index_pb2.PutNewRequest(url=url))

    def search_words(self, words):
        """ Pesquisa palavras via Gateway """
        response = self.gateway_stub.searchWord(
            index_pb2.SearchWordRequest(words=words))
        return response.urls

    def search_backlinks(self, url):
        """ Pesquisa backlinks para um URL via Gateway """
        response = self.gateway_stub.searchBacklinks(
            index_pb2.SearchBacklinksRequest(url=url))
        return response.backlinks

    def formatStats(self, data):
        """ Formata as stats para envio por websocket """
        stats = {
            "type": "stats",
            "top_queries": list(data.top_queries),
            "barrels": [
                {
                    "ip": barrel.address,
                    "size_words": barrel.index_size_words,
                    "size_urls": barrel.index_size_urls
                }
                for barrel in data.barrels
            ],
            "avg_response_times": {
                barrel.address: barrel.avg_response_time
                for barrel in data.barrels
            }
        }

        json_data = json.dumps(stats)

        return json_data

    def start_sending_statistics(self):
        """ Faz uma chamada RPC para a Gateway iniciar o envio de estatísticas """
        response = self.gateway_stub.startSendingStatistics(
            index_pb2.WebServerInfo(host=self.host, port=self.port))

        json_data = self.formatStats(response)

        asyncio.run(broadcast_message(json_data))

    def SendStats(self, request, context):
        """ Função para estatisticas em tempo real através de websocket """
        json_data = self.formatStats(request)

        asyncio.run(broadcast_message(json_data))
        return empty_pb2.Empty()


def run(host, port, host_gateway, port_gateway):
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        webserver = WebSever(host, port, host_gateway, port_gateway)
        index_pb2_grpc.add_IndexServicer_to_server(webserver, server)

        server.add_insecure_port(f"{host}:{port}")
        server.start()
        print(f"Web Server RPC started on {host}:{port}")
        server.wait_for_termination()

    except KeyboardInterrupt:
        print("\nStopping the Gateway...")
        return
