import grpc
from google.protobuf import empty_pb2
import index_pb2
import index_pb2_grpc
import requests
from bs4 import BeautifulSoup as jsoup
import re
import time
import random

INDEX_SERVERS = [
    "localhost:8183",
    "localhost:8184",
    "localhost:8185"
]


def choose_index_server(url):
    """Escolhe um Index Server baseado no hash da URL para distribuição uniforme."""
    return INDEX_SERVERS[hash(url) % len(INDEX_SERVERS)]

def extract_words(html):
    soup = jsoup(html, 'html.parser')
    text = soup.get_text()
    words = re.findall(r'\b\w{3,}\b', text.lower())  # Palavras com 3+ letras
    return set(words)

def extract_links(html, base_url):
    soup = jsoup(html, 'html.parser')
    links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('http'):
            links.add(href)
    return links

def run():
    gateway_channel = grpc.insecure_channel('localhost:8190')  # Conectar à Gateway
    gateway_stub = index_pb2_grpc.IndexStub(gateway_channel)
    
    while True:
        try:
            try:
                response = gateway_stub.takeNext(empty_pb2.Empty())  # Pede um URL da fila
                url = response.url
                
                if not url:
                   continue
                
                print(f"Processando URL: {url}")
                
                try:
                    # Fetch webpage using requests and parse with BeautifulSoup
                    response = requests.get(url)
                    response.raise_for_status()  # Raise an exception for bad status codes
                    soup = jsoup(response.text, 'html.parser')
                    
                    words = extract_words(response.text)
                    links = extract_links(response.text, url)
                            
                    while True:
                        server = random.choice(INDEX_SERVERS)
                        print(server)
                        try:
                            with grpc.insecure_channel(server) as channel:
                                index_stub = index_pb2_grpc.IndexStub(channel)
                                for word in words:
                                    index_stub.addToIndex(index_pb2.AddToIndexRequest(word=word, url=url))
                            print("DONE")
                            break
                        except grpc.RpcError:
                            print("ERRO AO CONNECTAR SERVIDOR")
                            pass
                
                    for link in links:
                        gateway_stub.putNew(index_pb2.PutNewRequest(url=link))

                except requests.RequestException as e:
                    print(f"Error fetching webpage: {e}")
                
            except grpc.RpcError as e:
                print(f"RPC failed: {e.code()}")
                print(f"RPC error details: {e.details()}")
                raise
                    
        except KeyboardInterrupt:
            print("\nStopping the robot...")
            return
        
if __name__ == '__main__':
    run()
