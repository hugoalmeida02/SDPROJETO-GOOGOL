import asyncio
import threading
from typing import Set
from fastapi import WebSocket

connected_clients: Set[WebSocket] = set()
connected_clients_lock = threading.Lock()

async def add_client(websocket: WebSocket):
    with connected_clients_lock:
        connected_clients.add(websocket)

async def remove_client(websocket: WebSocket):
    with connected_clients_lock:
        connected_clients.discard(websocket)
    try:
        await websocket.close()
    except:
        pass

async def broadcast_message(message: str):
    with connected_clients_lock:
        clients = connected_clients.copy()
    for client in clients:
        try:
            await client.send_text(message)
        except:
            await remove_client(client)