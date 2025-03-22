import grpc
import index_pb2
import index_pb2_grpc
from google.protobuf import empty_pb2

def run():
    channel = grpc.insecure_channel('localhost:8190')
    stub = index_pb2_grpc.IndexStub(channel)
    
    print("##### Menu Client #####")
    print("1 - Adicionar Url à Queue")
    print("2 - Pesquisar palavras")
    print("3 - Pesquisar backlinks")
    print("4 - Consultar estatísticas")
    print("5 - Sair")
                
    while True:
        try:
            try:
                print("Escolhe uma opcão de 1 a 5")
                option = input()
                
                if option == "1":
                    while True:
                        url = input()
                        if url.startswith("http"):
                            stub.putNew(index_pb2.PutNewRequest(url=url))
                            break
                        else: 
                            print("Url inválido! Tenta novamente")
                elif option == "2":
                    words = input()
                    response = stub.searchWord(index_pb2.SearchWordRequest(words=words))
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
                elif option == "3":
                    while True:
                        url = input()
                        if url.startswith("http"):
                            break
                        else: 
                            print("Url inválido! Tenta novamente")
                    response = stub.searchBacklinks(index_pb2.SearchBacklinksRequest(url=url))
                    if response.backlinks:
                        print(f"A url '{url}' foi encontrada nos seguintes URLs:")
                        for backlinks in response.backlinks:
                            print(f" Url - {backlinks}")
                    else:
                        print(f"Nenhum resultado encontrado para '{option}'.")
                elif option == "4":
                    print("Estatísticas")
                elif option == "5":
                    print("\nStopping the client...")
                    return
                else:
                    print("Opção inválida! Tenta novamente")
            except grpc.RpcError as e:
                print(f"RPC failed: {e.code()}")
                print(f"RPC error details: {e.details()}")
                return
        except KeyboardInterrupt:
            print("\nStopping the client...")
            return

if __name__ == "__main__":
    run()