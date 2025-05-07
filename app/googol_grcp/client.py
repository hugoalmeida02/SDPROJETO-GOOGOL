import grpc
from ..index_pb2 import index_pb2, index_pb2_grpc
from google.protobuf import empty_pb2
import time
import argparse


def run(host_gateway, port_gateway):
    channel = grpc.insecure_channel(f"{host_gateway}:{port_gateway}")
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
                    response = stub.searchWord(
                        index_pb2.SearchWordRequest(words=words))
                    if response.urls:
                        print(
                            f"A pesquisa '{words}' foi encontrada nos seguintes URLs:")
                        paginas = [response.urls[i:i + 10]
                                   for i in range(0, len(response.urls), 10)]
                        for i, pagina in enumerate(paginas):
                            print(f"Página {i+1}:")
                            for urls in pagina:
                                print(f" Url - {urls.url}")
                                print(f" Title - {urls.title}")
                                print(f" Quote - {urls.quote}")
                                print()
                    else:
                        print(f"Nenhum resultado encontrado para '{words}'.")
                elif option == "3":
                    while True:
                        url = input()
                        if url.startswith("http"):
                            break
                        else:
                            print("Url inválido! Tenta novamente")
                    response = stub.searchBacklinks(
                        index_pb2.SearchBacklinksRequest(url=url))
                    if response.backlinks:
                        print(
                            f"A url '{url}' foi encontrada nos seguintes URLs:")
                        for backlinks in response.backlinks:
                            print(f" Url - {backlinks}")
                    else:
                        print(f"Nenhum resultado encontrado para '{url}'.")
                elif option == "4":
                    response = stub.getStats(empty_pb2.Empty())
                    print("\nTop 10 pesquisas mais comuns:")
                    for i, term in enumerate(response.top_queries, 1):
                        print(f"{i}. {term}")

                    if response.barrels:
                        print("\nIndex Barrels ativos:")
                        for barrel in response.barrels:
                            print(
                                f"{barrel.address} — Entradas palavras: {barrel.index_size_words} — Entradas Backlings: {barrel.index_size_urls} — {barrel.avg_response_time:.3f} décimas")
                    else:
                        print("\nNenhum Index Barrels ativo.")
                elif option == "5":
                    print("\nStopping the client...")
                    return
                else:
                    print("Opção inválida! Tenta novamente")
            except grpc.RpcError as e:
                if e.details().startswith("WSASend: Connection reset"):
                    time.sleep(2)
                    print("Falha na ligação tente novamente")
                    channel = grpc.insecure_channel(
                        f"{host_gateway}:{port_gateway}")
                    stub = index_pb2_grpc.IndexStub(channel)
                else:
                    print(f"RPC failed: {e.code()}")
                    print(f"RPC error details: {e.details()}")
        except KeyboardInterrupt:
            print("\nStopping the client...")
            return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Client")
    parser.add_argument("--host_gateway", type=str, required=True,
                        help="Host para a gateway gRPC")
    parser.add_argument("--port_gateway", type=str, required=True,
                        help="Porta para a gateway gRPC")
    args = parser.parse_args()

    run(args.host_gateway, args.port_gateway)
