import logging
import os
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.rate_limit import limiter
from app.routers import feedback, futebol, lotteries, totobola

log = logging.getLogger("desdobra1x2")

MAX_BODY_BYTES = 200_000  # plenty for any legitimate request this app makes (docs/plano-seguranca.md)

app = FastAPI(title="desdobra1X2")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    # Comma-separated list, e.g. "https://myapp.vercel.app,http://localhost:5173"
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_BODY_BYTES:
        return JSONResponse(status_code=413, content={"detail": "Pedido demasiado grande."})
    return await call_next(request)


@app.exception_handler(StarletteHTTPException)
async def sanitize_server_errors(request: Request, exc: StarletteHTTPException):
    """5xx responses never repeat the raw exception text to the client (docs/plano-seguranca.md)."""
    if exc.status_code >= 500:
        ref = uuid.uuid4().hex[:8]
        log.error("ref=%s path=%s status=%s detail=%s", ref, request.url.path, exc.status_code, exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": f"Não foi possível processar o pedido agora. (ref: {ref})"},
        )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)


@app.exception_handler(Exception)
async def catch_unhandled(request: Request, exc: Exception):
    ref = uuid.uuid4().hex[:8]
    log.exception("unhandled error ref=%s path=%s", ref, request.url.path)
    return JSONResponse(status_code=500, content={"detail": f"Erro interno. (ref: {ref})"})


app.include_router(totobola.router)
app.include_router(lotteries.router)
app.include_router(futebol.router)
app.include_router(feedback.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
