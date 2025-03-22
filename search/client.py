import grpc
import index_pb2
import index_pb2_grpc
from google.protobuf import empty_pb2

def run():
    channel = grpc.insecure_channel('localhost:8190')
    stub = index_pb2_grpc.IndexStub(channel)
    
    while True:
        try:
            try:
                option = input()
                
                if option.startswith("http"):
                    stub.putNew(index_pb2.PutNewRequest(url=option))
                    
                else:
                    response = stub.searchWord(index_pb2.SearchWordRequest(words=option))
                    if response.urls:
                        print(f"A palavra '{option}' foi encontrada nos seguintes URLs:")
                        paginas = [response.urls[i:i + 10] for i in range(0, len(response.urls), 10)]
                        for i, pagina in enumerate(paginas):
                            print(f"Página {i+1}:")
                            for urls in pagina:
                                print(f" Url - {urls.url}")
                                print(f" Title - {urls.title}")
                                print(f" Quote - {urls.quote}")
                                print()
                    else:
                        print(f"Nenhum resultado encontrado para '{option}'.")
            except grpc.RpcError as e:
                print(f"RPC failed: {e.code()}")
                print(f"RPC error details: {e.details()}")
                return
        except KeyboardInterrupt:
            print("\nStopping the client...")
            return

if __name__ == "__main__":
    run()