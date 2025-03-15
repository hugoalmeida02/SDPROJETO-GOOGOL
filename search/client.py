import grpc
import index_pb2
import index_pb2_grpc
import time
from google.protobuf import empty_pb2

def run():
    server_ip = input("Digite o IP do servidor (ex: 192.168.0.3) ou pressione Enter para localhost: ")
    if not server_ip:
        server_ip = "localhost"
    
    channel = grpc.insecure_channel(f'{server_ip}:8190')  # Conectar ao Gateway
    stub = index_pb2_grpc.IndexStub(channel)
    
    while True:
        print("\n### Menu Cliente ###")
        print("1 - Adicionar URL para indexação")
        print("2 - Pesquisar palavra no índice")
        print("3 - Ver estatísticas do servidor")
        print("4 - Sair")
        
        option = input("Escolha uma opção: ")
        
        if option == "1":
            url = input("Digite a URL: ")
            if url.startswith("http"):
                stub.putNew(index_pb2.PutRequest(item=url))
                print(f"URL '{url}' adicionada para indexação.")
            else:
                print("URL inválida! Deve começar com 'http'.")
        
        elif option == "2":
            word = input("Digite a palavra para pesquisar: ")
            response = stub.searchWord(index_pb2.SearchWordRequest(word=word))
            if response.urls:
                print(f"A palavra '{word}' foi encontrada nos seguintes URLs:")
                for url in response.urls:
                    print(f" - {url}")
            else:
                print(f"Nenhum resultado encontrado para '{word}'.")
        
        elif option == "3":
            print("Monitorizando estatísticas do servidor...")
            try:
                response = stub.getStats(empty_pb2.Empty())
                print(f"URLs indexadas: {response.total_urls}")
                print(f"Palavras únicas indexadas: {response.total_words}")
                print(f"Memória usada: {response.memory_usage} bytes")
                print(f"Velocidade de indexação: {response.pages_per_second:.2f} páginas/segundo")
            except grpc.RpcError as e:
                print(f"Erro ao obter estatísticas: {e.details()}")
                
        elif option == "4":
            print("Encerrando o cliente...")
            break
        
        else:
            print("Opção inválida! Escolha uma opção entre 1 e 4.")

if __name__ == "__main__":
    run()