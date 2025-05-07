from fastapi import FastAPI, Request, Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .grpc_client import put_new_url, search_words, search_backlinks

app = FastAPI()

# Diretórios para templates e ficheiros estáticos
templates = Jinja2Templates(directory="app/googol_web/templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
