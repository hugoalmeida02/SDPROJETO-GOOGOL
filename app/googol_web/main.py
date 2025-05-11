import asyncio
import grpc
from concurrent import futures
from fastapi import FastAPI
import uvicorn
from .routes import router
from .webserver import WebSever
from ..index_pb2 import index_pb2, index_pb2_grpc
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import argparse

from .context import set_webserver

app = FastAPI()
app.include_router(router)

app.mount("/static", StaticFiles(directory="app/googol_web/static"), name="static")

# Inicializa o WebSever antes de iniciar o servidor HTTP
def initialize_webserver(args):
    webserver = WebSever(args.host, args.port, args.host_gateway, args.port_gateway)
    set_webserver(webserver)  # Definir o webserver para uso global
    return webserver

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

async def main(webserver):

    # Executar gRPC em background
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, start_grpc_server, webserver)

    # Iniciar FastAPI com uvicorn
    config = uvicorn.Config("app.googol_web.main:app", host="localhost", port=8080, reload=True)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    # Argumentos de linha de comando
    parser = argparse.ArgumentParser(description="Web Server")
    parser.add_argument("--host", type=str, required=True, help="Host para o servidor gRPC")
    parser.add_argument("--port", type=str, required=True, help="Porta para o servidor gRPC")
    parser.add_argument("--host_gateway", type=str, required=True, help="Host para o servidor gRPC")
    parser.add_argument("--port_gateway", type=str, required=True, help="Porta para o servidor gRPC")
    args = parser.parse_args()
    
    webserver = initialize_webserver(args)
    
    # Iniciar o servidor
    asyncio.run(main(webserver))
