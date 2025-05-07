from fastapi import FastAPI, WebSocket, Request, Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import asyncio

from .grpc_client import put_new_url, search_words, search_backlinks, get_system_stats
from .utils.hackernews_api import search_hackernews
from .utils.openai_api import get_openai_summary

app = FastAPI()

# Diretórios para templates e ficheiros estáticos
templates = Jinja2Templates(directory="app/googol_web/templates")
app.mount("/static", StaticFiles(directory="app/googol_web/static"), name="static")

# # Lista para guardar WebSocket connections
# websocket_connections = []


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     websocket_connections.append(websocket)
#     try:
#         while True:
#             await asyncio.sleep(5)  # Atualiza a cada 5 segundos
#             stats = get_system_stats()
#             message = format_stats(stats)
#             await websocket.send_text(message)
#     except:
#         websocket_connections.remove(websocket)


# def format_stats(stats):
#     """Formata as estatísticas para texto simples para o frontend."""
#     msg = "📈 Estatísticas do Googol:\n\n"
#     msg += "🔟 Top Pesquisas:\n"
#     for term in stats.top_queries:
#         msg += f" - {term}\n"

#     msg += "\n🖥️ Index Barrels:\n"
#     for barrel in stats.barrels:
#         msg += f" - {barrel.address} ➔ {barrel.index_size} entradas ➔ {barrel.avg_response_time:.1f} décimas\n"

#     return msg


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
    # hn_stories = search_hackernews(words)  # Pesquisa Hacker News
    # openai_summary = get_openai_summary(words)  # Gera resumo OpenAI
    return templates.TemplateResponse("results.html", {"request": request, "words": words, "urls": urls})


@app.get("/search-backlinks", response_class=HTMLResponse)
async def backlinks(request: Request, url: str):
    print(f"Consulta recebida: {url}")
    backlinks = search_backlinks(url)  # Chamar o grpc_client
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
