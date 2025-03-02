from xmlrpc.server import SimpleXMLRPCServer
from index import InvertedIndex

index = InvertedIndex()

def add_page(url, text):
    index.add_page(url, text)
    return True

def search(query):
    return list(index.search(query))

server = SimpleXMLRPCServer(("localhost", 8000))
server.register_function(add_page, "add_page")
server.register_function(search, "search")
print("Servidor a correr em http://localhost:8000...")
server.serve_forever()