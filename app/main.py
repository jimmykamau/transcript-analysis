from fastapi import FastAPI

from app.transcripts.router import router as transcripts_router

app = FastAPI(title="Transcript Analysis")

app.include_router(transcripts_router, prefix="/transcripts", tags=["transcripts"])


@app.get("/health")
async def health():
    return {"status": "ok"}
