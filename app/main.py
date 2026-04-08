from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymongo import AsyncMongoClient

from app.dependencies import get_settings
from app.transcripts.router import router as transcripts_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = (
        get_settings()
    )  # fail fast if required config (e.g. ANTHROPIC_API_KEY) is missing
    client = AsyncMongoClient(settings.mongodb_url, tz_aware=True)
    app.state.db = client[settings.mongodb_db_name]
    await app.state.db["transcripts"].create_index("topics")
    yield
    await client.close()


app = FastAPI(title="Transcript Analysis", lifespan=lifespan)

app.include_router(transcripts_router, prefix="/transcripts", tags=["transcripts"])


@app.get("/health")
async def health():
    return {"status": "ok"}
