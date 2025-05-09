import asyncio
import grpc
from concurrent import futures
from fastapi import FastAPI
import uvicorn
from .routes import router  # certifica-te que o path está correto
from .webserver import WebSever
from ..index_pb2 import index_pb2, index_pb2_grpc
from fastapi.staticfiles import StaticFiles

# Configurações
WEB_HOST = "localhost"
WEB_PORT = "8888"
GATEWAY_HOST = "localhost"
GATEWAY_PORT = "8190"

app = FastAPI()
app.include_router(router)

app.mount("/static", StaticFiles(directory="app/googol_web/static"), name="static")

def start_grpc_server():
    """Inicia o servidor gRPC num thread separado."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    grpc_service = WebSever(WEB_HOST, WEB_PORT, GATEWAY_HOST, GATEWAY_PORT)
    index_pb2_grpc.add_IndexServicer_to_server(grpc_service, server)
    server.add_insecure_port(f"{WEB_HOST}:{WEB_PORT}")
    server.start()
    print(f"[gRPC] Servidor gRPC iniciado em {WEB_HOST}:{WEB_PORT}")
    server.wait_for_termination()

async def main():
    loop = asyncio.get_event_loop()

    # Executar gRPC em background
    loop.run_in_executor(None, start_grpc_server)

    # Iniciar FastAPI com uvicorn
    config = uvicorn.Config("app.googol_web.main:app", host="localhost", port=8080, reload=True)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
