import asyncio
import grpc
from concurrent import futures
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
import argparse

from .context import set_webserver
from .routes import router
from .webserver import WebSever
from ..index_pb2 import index_pb2_grpc

app = FastAPI()

# Monta o diretório de ficheiros estáticos (CSS/JS)
app.mount("/static", StaticFiles(directory="app/googol_web/static"), name="static")

# Adiciona as rotas definidas
app.include_router(router)

# Inicializa o WebSever antes de iniciar o servidor HTTP
def initialize_webserver(args):
    webserver = WebSever(args.host_webserver, args.port_webserver, args.host_gateway, args.port_gateway)
    set_webserver(webserver)  # Definir o webserver para uso global
    return webserver

# Inicia o servidor gRPC que escuta chamadas da Gateway
def start_grpc_server(webserver):
    """Inicia o servidor gRPC num thread separado."""
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        index_pb2_grpc.add_IndexServicer_to_server(webserver, server)
        server.add_insecure_port(f"{webserver.host}:{webserver.port}")
        server.start()
        print(f"WebServer iniciado em {webserver.host}:{webserver.port}")
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nStopping the WebServer...")

# Função principal que inicia FastAPI e gRPC em paralelo
async def main(webserver, host, port):

    # Executar gRPC em background
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, start_grpc_server, webserver)

    # Iniciar FastAPI com uvicorn
    config = uvicorn.Config("app.googol_web.main:app", host=host, port=port, reload=True)
    server = uvicorn.Server(config)
    await server.serve()

# Execução principal para correr o servidor com argumentos
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WebServer e RESTAPI")
    parser.add_argument("--host_api", type=str, required=True, help="Host para a REST API")
    parser.add_argument("--port_api", type=str, required=True, help="Porta para a REST API")
    parser.add_argument("--host_webserver", type=str, required=True, help="Host para o webserver")
    parser.add_argument("--port_webserver", type=str, required=True, help="Porta para o webserver")
    parser.add_argument("--host_gateway", type=str, required=True, help="Host para a gateway")
    parser.add_argument("--port_gateway", type=str, required=True, help="Porta para a gateway")
    args = parser.parse_args()
    
    webserver = initialize_webserver(args)
    
    # Iniciar o servidor
    asyncio.run(main(webserver, args.host_api, int(args.port_api)))
