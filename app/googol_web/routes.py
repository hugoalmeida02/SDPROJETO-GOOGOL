from fastapi import APIRouter, Request, WebSocket, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Set
import threading
import asyncio
import grpc

from .websockets import add_client, remove_client
from .utils.openai_api import generate_analysis
from .utils.hackernews_api import index_top_stories
from .context import get_webserver


router = APIRouter()
templates = Jinja2Templates(directory="app/googol_web/templates")


# Conjunto de clientes conectados por WebSocket
connected_clients: Set[WebSocket] = set()
connected_clients_lock = threading.Lock()


# Página inicial
@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Endpoint para submeter novo URL
@router.post("/add-url")
async def add_url(request: Request, url: str = Form(...)):
    webserver = get_webserver()
    if url:
        print(f"URL recebido para indexação: {url}")
        response = webserver.put_new_url(url)
        
        if response:
            return {"message": "URL adicionado com sucesso"}
        else:
            return {"message": "Falha ao adicionar ur! Tente novamente"}
    else:
        return {"error": "URL inválido"}


# Pesquisa por palavras com paginação
@router.get("/search", response_class=HTMLResponse)
async def search(request: Request, words: str, page: int = 1):
    webserver = get_webserver()
    response = webserver.search_words(words)
    
    if response[0]:
        results = response[1]
        per_page = 10

        # Paginação
        start = (page - 1) * per_page
        end = start + per_page
        paginated = results[start:end]
        total_pages = (len(results) + per_page - 1) // per_page

        return templates.TemplateResponse("results.html", {
            "request": request,
            "words": words,
            "urls": paginated,
            "current_page": page,
            "total_pages": total_pages
        })
    else:
        return templates.TemplateResponse("falha.html", {"request": request})
        
            


# Indexação de URLs do Hacker News com base em termos pesquisados
@router.post("/index_hackernews_urls")
async def index_hackernews_urls(request: Request):
    search_terms = request.query_params.get('words', '').split()
    urls = index_top_stories(search_terms)

    webserver = get_webserver()
    for url in urls:
        webserver.put_new_url(url)

    return JSONResponse({"urls": urls, "count": len(urls)})


# Endpoint para gerar análise textual com OpenAI
@router.post("/generate_analysis")
async def generate_analysis_endpoint(request: Request):
    try:
        data = await request.json()
        search_terms = data.get("search_terms")

        analysis = await generate_analysis(search_terms)

        return JSONResponse(content={"analysis": analysis})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Erro ao gerar a análise: {str(e)}"})


# Pesquisa de backlinks
@router.get("/search-backlinks", response_class=HTMLResponse)
async def backlinks(request: Request, url: str):
    webserver = get_webserver()
    response = webserver.search_backlinks(url)
    if response[0]:
        backlinks = response[1]
        return templates.TemplateResponse("backlinks.html", {"request": request, "url": url, "backlinks": backlinks})
    else:
        return templates.TemplateResponse("falha.html", {"request": request})
    


# Endpoint WebSocket para enviar estatísticas em tempo real
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
