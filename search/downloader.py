import grpc
from google.protobuf import empty_pb2
import index_pb2
import index_pb2_grpc
import requests
from bs4 import BeautifulSoup as jsoup
import re
import time
import random
import argparse


def extract_info(html, base_url):
    """ Extrai a informação de uma página """
    soup = jsoup(html, 'html.parser')
    links = set()
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('http'):
            links.add(href)
            
    text = soup.get_text()
    words = re.findall(r'\b\w{3,}\b', text.lower())  # Palavras com 3+ letras
    
    title = soup.title.string if soup.title else 'Título não encontrado'
    quote = soup.find('p').text if soup.find('p') else 'Citação não encontrada'
    
    return set(words), links, title, quote

def run(host_gateway, port_gateway, host_url_queue, port_url_queue):
    url_queue_channel = grpc.insecure_channel(f"{host_url_queue}:{port_url_queue}")  # Conectar à queue
    url_queue_stub = index_pb2_grpc.IndexStub(url_queue_channel)
    gateway_channel = grpc.insecure_channel(f"{host_gateway}:{port_gateway}")  # Conectar à gateway
    gateway_stub = index_pb2_grpc.IndexStub(gateway_channel)

    while True:
        try:
            try:
                response = url_queue_stub.takeNext(empty_pb2.Empty())  # Pede um URL da fila
            except:
                time.sleep(2)
                print("Tentando reconectar à url_queue")
                url_queue_channel = grpc.insecure_channel(f"{host_url_queue}:{port_url_queue}")  # Conectar à queue
                url_queue_stub = index_pb2_grpc.IndexStub(url_queue_channel)
                continue
            
            url = response.url
            print(f"Processando URL: {url}")
            
            if not url:
                continue
            
            try:
                # Fetch webpage using requests and parse with BeautifulSoup
                response = requests.get(url)
                response.raise_for_status()  # Raise an exception for bad status codes
                
                words, links, title, quote = extract_info(response.text, url)
                
                while True:
                    try:
                        response = gateway_stub.getIndexBarrels(empty_pb2.Empty())
                    except:
                        time.sleep(2)
                        print("Tentando reconectar à gateway")
                        gateway_channel = grpc.insecure_channel(f"{host_gateway}:{port_gateway}")  # Conectar à gateway
                        gateway_stub = index_pb2_grpc.IndexStub(gateway_channel)
                        continue
                    
                    SERVERS = [] #Guarda os Index Barrels ativos
                    
                    for server in response.indexInfos:
                        if server not in SERVERS:
                            SERVERS.append(server)
                            
                    if len(SERVERS) != 0:
                        server_index = random.randint(0, len(SERVERS) - 1)

                        server = SERVERS[server_index]
                        try:
                            with grpc.insecure_channel(server) as channel:
                                print(f"Connectado server {server}")
                                index_stub = index_pb2_grpc.IndexStub(channel)
                                
                                for word in words:
                                    index_stub.addToIndexWords(index_pb2.AddToIndexRequestWords(word=word, url=url, from_multicast=False))
                                    
                                for link in links:   
                                    index_stub.addToIndexLinks(index_pb2.AddToIndexRequestLinks(url=url, title=title, quote=quote,  link=link, from_multicast=False))
                                
                            for link in links:   
                                url_queue_stub.putNew(index_pb2.PutNewRequest(url=link))
                                    
                        except grpc.RpcError as e:
                            print(f"Erro server {server}")
                    
                        break
                    else:
                        print("Nenhum Index Barrel disponivel")
                
            except requests.RequestException as e:
                print(f"Error fetching webpage: {e}")
                 
        except KeyboardInterrupt:
            print("\nStopping the robot...")
            return
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Downloader")
    parser.add_argument("--host_gateway", type=str, required=True,
                        help="Host para a gateway gRPC")
    parser.add_argument("--port_gateway", type=str, required=True,
                        help="Porta para a gateway gRPC")
    parser.add_argument("--host_url_queue", type=str, required=True,
                        help="Host para a url_queue gRPC")
    parser.add_argument("--port_url_queue", type=str, required=True,
                        help="Porta para a url_queue gRPC")
    args = parser.parse_args()
    
    run(args.host_gateway, args.port_gateway, args.host_url_queue, args.port_url_queue)
