import grpc
from google.protobuf import empty_pb2
import index_pb2
import index_pb2_grpc
import requests
from bs4 import BeautifulSoup as jsoup
import re

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
    # Create a gRPC channel
    channel = grpc.insecure_channel('localhost:8183')
    
    # Create a stub (client)
    stub = index_pb2_grpc.IndexStub(channel)
    
    while True:
        try:
            try:
                response = stub.takeNext(empty_pb2.Empty())
                url = response.url
                print(f"Received URL: {url}")
                
                try:
                    # Fetch webpage using requests and parse with BeautifulSoup
                    response = requests.get(url)
                    response.raise_for_status()  # Raise an exception for bad status codes
                    soup = jsoup(response.text, 'html.parser')
                    
                    words = extract_words(response.text)
                    links = extract_links(response.text, url)
                    
                    
                    for word in words:
                        stub.addToIndex(index_pb2.AddToIndexRequest(word=word, url=url))
                
                    for link in links:
                        stub.putNew(index_pb2.PutNewRequest(url=link))

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
