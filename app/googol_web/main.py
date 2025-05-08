from fastapi import FastAPI
from .routes import router

app = FastAPI()

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("googol_web.main:app", host="0.0.0.0", port=8080, reload=True)