import grpc
import index_pb2
import index_pb2_grpc
from google.protobuf import empty_pb2

# Definir a gateway a ligar
GATEWAY_ADDRESS = "localhost:8190"  # Atualiza se necessário

def get_gateway_stub():
    """ Cria uma ligação à gateway """
    channel = grpc.insecure_channel(GATEWAY_ADDRESS)
    stub = index_pb2_grpc.IndexStub(channel)
    return stub

def put_new_url(url):
    """ Envia novo URL para a fila de URLs (via Gateway) """
    stub = get_gateway_stub()
    stub.putNew(index_pb2.PutNewRequest(url=url))

def search_words(words):
    """ Pesquisa palavras via Gateway """
    stub = get_gateway_stub()
    response = stub.searchWord(index_pb2.SearchWordRequest(words=words))
    return response.urls

def get_system_stats():
    """ Vai buscar as estatísticas do sistema à Gateway """
    stub = get_gateway_stub()
    response = stub.getStats(empty_pb2.Empty())
    return response
