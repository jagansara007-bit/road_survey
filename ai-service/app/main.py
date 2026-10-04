
import os

from app.api.errors import APIError, api_error_handler, generic_error_handler
from app.api.routes import router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Road Damage AI Microservice", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(Exception, generic_error_handler)

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return HTMLResponse("<h1>Road Damage AI Microservice</h1><p><a href='/docs'>Swagger API Docs</a></p>")

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

app.include_router(router, prefix="/api/v1")
app.include_router(router)
