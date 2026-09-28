import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import feedback, futebol, lotteries, totobola

app = FastAPI(title="desdobra1X2")

app.add_middleware(
    CORSMiddleware,
    # Comma-separated list, e.g. "https://myapp.vercel.app,http://localhost:5173"
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(totobola.router)
app.include_router(lotteries.router)
app.include_router(futebol.router)
app.include_router(feedback.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
