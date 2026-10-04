
from app.api.errors import APIError, api_error_handler, generic_error_handler
from app.api.routes import router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

app.include_router(router, prefix="/api/v1")
app.include_router(router)
