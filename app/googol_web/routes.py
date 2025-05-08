from fastapi import APIRouter, Request, Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .grpc_client import put_new_url, search_words, search_backlinks, get_system_stats

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/add-url")
async def add_url(request: Request, payload: dict = Body(...)):
    url = payload.get("url")
    if url:
        print(f"URL recebido para indexação: {url}")
        put_new_url(url)
        return {"message": "URL adicionado com sucesso"}
    else:
        return {"error": "URL inválido"}
    

@router.get("/search", response_class=HTMLResponse)
async def search(request: Request, words: str):
    print(f"Pesquisa recebida: {words}")
    urls = search_words(words)  # Faz a pesquisa real via gRPC
    return templates.TemplateResponse("results.html", {"request": request, "words": words, "urls": urls})


@router.get("/search-backlinks", response_class=HTMLResponse)
async def backlinks(request: Request, url: str):
    print(f"Consulta recebida: {url}")
    backlinks = search_backlinks(url)  # Faz a pesquisa real via gRPC
    return templates.TemplateResponse("backlinks.html", {"request": request, "url": url, "backlinks": backlinks})