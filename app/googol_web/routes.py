from fastapi import APIRouter, Request, Body, WebSocket, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .webserver import WebSever
from .websockets import add_client, remove_client
from .utils.openai_api import generate_analysis
from .utils.hackernews_api import index_user_stories, index_top_stories
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
async def search(request: Request, words: str, page: int = 1):
    results = webserver.search_words(words)
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
    
@router.post("/generate_analysis")
async def generate_analysis_endepoint(request):
    try:
        analysis = generate_analysis(request.search_terms)
        return {"analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/search-backlinks", response_class=HTMLResponse)
async def backlinks(request: Request, url: str):
    print(f"Consulta recebida: {url}")
    backlinks = webserver.search_backlinks(url)
    return templates.TemplateResponse("backlinks.html", {"request": request, "url": url, "backlinks": backlinks})
        

@router.post("/index_hackernews_urls")
async def index_hackernews_urls(request: Request):
    search_terms = request.query_params.get('words', '').split()
    
    # Chama a função que já criaste para pegar as "top stories" e filtrar
    urls = index_top_stories(search_terms)

    return templates.TemplateResponse("results.html", {
        "request": request,
        "words": search_terms,
        "urls": urls,
        "summary": "Análise gerada pela IA."
    })


@router.post("/index_hackernews_urls_user")
async def index_hackernews_urls_user(request: Request, user_id: str = Form(...), ):
    search_terms = request.query_params.get('words', '').split()
    
    # Chama a função que já criaste para pegar as stories de um utilizador e filtrar
    urls = index_user_stories(user_id, search_terms)
    
    return templates.TemplateResponse("results.html", {
        "request": request,
        "words": search_terms,
        "urls": urls,
        "summary": "Análise gerada pela IA."
    })


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