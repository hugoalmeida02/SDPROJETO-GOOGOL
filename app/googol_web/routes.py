from fastapi import APIRouter, Request, Body, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .webserver import WebSever

import asyncio
from typing import Dict, Set
import threading

router = APIRouter()

templates = Jinja2Templates(directory="app/googol_web/templates")

webserver = WebSever("localhost", "8888", "localhost", "8190")  # ajusta a porta

# # Store all connected clients
# connected_clients: Set[WebSocket] = set()
# connected_clients_lock = threading.Lock()

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



# class WebSocketBridge(stomp.ConnectionListener):
#     def __init__(self, websocket: WebSocket):
#         self.websocket = websocket
        
#     def on_message(self, frame):
#         # Reverse the message and broadcast to all clients
#         message = frame.body
#         asyncio.create_task(broadcast_message(message))

# async def add_client(websocket: WebSocket):
#     with connected_clients_lock:
#         connected_clients.add(websocket)

# async def remove_client(websocket: WebSocket):
#     with connected_clients_lock:
#         connected_clients.discard(websocket)
#     try:
#         await websocket.close()
#     except:
#         pass

# async def broadcast_message(message: str):
#     with connected_clients_lock:
#         clients = connected_clients.copy()
#     for client in clients:
#         try:
#             await client.send_text(message)
#         except:
#             await remove_client(client)
    
# @router.websocket("/websocket")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     await add_client(websocket)
    
#     try:
#         while True:
#             try:
#                 # Receive message from client
#                 data = await websocket.receive_text()
#                 if not data:
#                     continue
        
#                 # Broadcast message to all clients
#                 await broadcast_message(data)
                
#             except Exception as e:
#                 print(f"Error processing message: {e}")
#                 break
                
#     except Exception as e:
#         print(f"WebSocket error: {e}")
#     finally:
#         await remove_client(websocket)