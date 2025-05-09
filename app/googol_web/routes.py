from fastapi import APIRouter, Request, Body, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .webserver import WebSever
from .websockets import add_client, remove_client

import asyncio
from typing import Dict, Set
import threading

router = APIRouter()

templates = Jinja2Templates(directory="app/googol_web/templates")

webserver = WebSever("localhost", "8888", "localhost", "8190")  # ajusta a porta

# Store all connected clients
connected_clients: Set[WebSocket] = set()
connected_clients_lock = threading.Lock()

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/add-url")
async def add_url(request: Request, payload: dict = Body(...)):
    url = payload.get("url")
    if url:
        print(f"URL recebido para indexação: {url}")
        webserver.put_new_url(url)
        return {"message": "URL adicionado com sucesso"}
    else:
        return {"error": "URL inválido"}
    

@router.get("/search", response_class=HTMLResponse)
async def search(request: Request, words: str):
    print(f"Pesquisa recebida: {words}")
    urls = webserver.search_words(words)  # Faz a pesquisa real via gRPC
    return templates.TemplateResponse("results.html", {"request": request, "words": words, "urls": urls})


@router.get("/search-backlinks", response_class=HTMLResponse)
async def backlinks(request: Request, url: str):
    print(f"Consulta recebida: {url}")
    backlinks = webserver.search_backlinks(url)  # Faz a pesquisa real via gRPC
    return templates.TemplateResponse("backlinks.html", {"request": request, "url": url, "backlinks": backlinks})
        
@router.websocket("/websocket")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await add_client(websocket)
    
    try:
        while True:
            await asyncio.sleep(10)  
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await remove_client(websocket)