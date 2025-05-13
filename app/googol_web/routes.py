from fastapi import APIRouter, Request, Body, WebSocket, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates


from .websockets import add_client, remove_client
from .utils.openai_api import generate_analysis
from .utils.hackernews_api import index_top_stories
import asyncio
from typing import Dict, Set
import threading
from .context import get_webserver

router = APIRouter()
templates = Jinja2Templates(directory="app/googol_web/templates")

# Store all connected clients
connected_clients: Set[WebSocket] = set()
connected_clients_lock = threading.Lock()

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/add-url")
async def add_url(request: Request, url: str = Form(...)):
    webserver = get_webserver()
    if url:
        print(f"URL recebido para indexação: {url}")
        webserver.put_new_url(url)
        return {"message": "URL adicionado com sucesso"}
    else:
        return {"error": "URL inválido"}

@router.get("/search", response_class=HTMLResponse)
async def search(request: Request, words: str, page: int = 1):
    webserver = get_webserver()
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
    
# Endpoint para gerar a análise com base nos termos de pesquisa
@router.post("/generate_analysis")
async def generate_analysis_endpoint(request: Request):
    try:
        data = await request.json()
        search_terms = data.get("search_terms")
        
        if not search_terms:
            return JSONResponse(status_code=400, content={"error": "search_terms são obrigatórios"})
        
        analysis = await generate_analysis(search_terms)

        return JSONResponse(content={"analysis": analysis})
    
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Erro ao gerar a análise: {str(e)}"})
    
@router.get("/search-backlinks", response_class=HTMLResponse)
async def backlinks(request: Request, url: str):
    webserver = get_webserver()
    backlinks = webserver.search_backlinks(url)
    print(backlinks)
    return templates.TemplateResponse("backlinks.html", {"request": request, "url": url, "backlinks": backlinks})
        

@router.post("/index_hackernews_urls")
async def index_hackernews_urls(request: Request):
    search_terms = request.query_params.get('words', '').split()
    urls = index_top_stories(search_terms)
    
    webserver = get_webserver()
    for url in urls:
        webserver.put_new_url(url)
        
    return JSONResponse({"urls": urls, "count": len(urls)})


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