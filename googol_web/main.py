from fastapi import FastAPI, WebSocket, Request, Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import asyncio

from grpc_client import put_new_url, search_words, get_system_stats

app = FastAPI()

# Diretórios para templates e ficheiros estáticos
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Lista para guardar WebSocket connections
websocket_connections = []

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_connections.append(websocket)
    try:
        while True:
            await asyncio.sleep(1)
            # Por enquanto envia uma mensagem dummy
            await websocket.send_text("[Stat Update] Sistema ativo!")
    except:
        websocket_connections.remove(websocket)
        
@app.post("/add-url")
async def add_url(request: Request, payload: dict = Body(...)):
    url = payload.get("url")
    if url:
        print(f"✅ URL recebido para indexação: {url}")
        put_new_url(url)
        return {"message": "URL adicionado com sucesso"}
    else:
        return {"error": "URL inválido"}

@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, words: str):
    print(f"🔎 Pesquisa recebida: {words}")
    urls = search_words(words)
    return templates.TemplateResponse("results.html", {"request": request, "words": words})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
