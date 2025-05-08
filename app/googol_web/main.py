from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import asyncio
import json

from .grpc_client import put_new_url, search_words, search_backlinks, get_system_stats

app = FastAPI()

# Diretórios para templates e ficheiros estáticos
templates = Jinja2Templates(directory="app/googol_web/templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

clients = []  # Lista de clientes WebSocket conectados

@app.post("/add-url")
async def add_url(request: Request, payload: dict = Body(...)):
    url = payload.get("url")
    if url:
        print(f"URL recebido para indexação: {url}")
        put_new_url(url)
        return {"message": "URL adicionado com sucesso"}
    else:
        return {"error": "URL inválido"}
    

@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, words: str):
    print(f"Pesquisa recebida: {words}")
    urls = search_words(words)  # Faz a pesquisa real via gRPC
    return templates.TemplateResponse("results.html", {"request": request, "words": words, "urls": urls})


@app.get("/search-backlinks", response_class=HTMLResponse)
async def backlinks(request: Request, url: str):
    print(f"Consulta recebida: {url}")
    backlinks = search_backlinks(url)  # Faz a pesquisa real via gRPC
    return templates.TemplateResponse("backlinks.html", {"request": request, "url": url, "backlinks": backlinks})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(update_stats_loop())


async def update_stats_loop():
    previous = None
    while True:
        try:
            current = get_system_stats()
            if current != previous:
                previous = current
                for client in clients:
                    try:
                        await client.send_text(json.dumps(current))
                    except Exception:
                        clients.remove(client)
        except Exception as e:
            print(f"Erro ao atualizar estatísticas: {e}")
        await asyncio.sleep(3)