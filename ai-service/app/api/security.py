import hmac
import os

from app.api.errors import APIError
from fastapi import Header, Request

API_KEY = os.environ.get("API_KEY", "dev-secret-key")

def verify_api_key(x_api_key: str | None = Header(None)) -> str:
    if not x_api_key:
        raise APIError("Missing X-API-Key header", status_code=401)
        
    if not hmac.compare_digest(x_api_key.encode("utf-8"), API_KEY.encode("utf-8")):
        raise APIError("Invalid API Key", status_code=401)
        
    return x_api_key

def require_api_key(request: Request):
    if request.url.path == "/health":
        return
    verify_api_key(request.headers.get("x-api-key"))
