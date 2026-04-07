from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.dependencies import get_settings
from app.transcripts.router import router as transcripts_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings()  # fail fast if required config (e.g. ANTHROPIC_API_KEY) is missing
    yield


app = FastAPI(title="Transcript Analysis", lifespan=lifespan)

app.include_router(transcripts_router, prefix="/transcripts", tags=["transcripts"])


@app.get("/health")
async def health():
    return {"status": "ok"}
