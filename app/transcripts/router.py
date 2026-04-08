from typing import Annotated

import anthropic
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.config import Settings
from app.dependencies import get_settings
from app.transcripts import repository, services
from app.transcripts.models import TranscriptDocument
from app.transcripts.schemas import (
    AnalyzeResponse,
    TranscriptRequest,
    TranscriptSearchRequest,
    TranscriptSummary,
)

router = APIRouter()

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_db(request: Request):
    return request.app.state.db


DbDep = Annotated[object, Depends(get_db)]


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: TranscriptRequest, settings: SettingsDep, db: DbDep):
    try:
        analysis = await services.analyze_transcript(request.transcript, settings)
    except anthropic.AuthenticationError as err:
        raise HTTPException(
            status_code=500, detail="Service configuration error"
        ) from err
    except (anthropic.APIStatusError, anthropic.APIConnectionError) as err:
        raise HTTPException(status_code=502, detail="Upstream API error") from err
    except ValueError as err:
        raise HTTPException(
            status_code=500, detail="Unexpected response from LLM"
        ) from err

    try:
        saved = await repository.save_transcript(db, request.transcript, analysis)
    except Exception as err:
        raise HTTPException(status_code=503, detail="Storage unavailable") from err

    return AnalyzeResponse(**saved.model_dump())


@router.get("/topics", response_model=list[str])
async def list_topics(db: DbDep):
    try:
        return await repository.list_topics(db)
    except Exception as err:
        raise HTTPException(status_code=503, detail="Storage unavailable") from err


@router.post("/search", response_model=list[TranscriptSummary])
async def search_transcripts(
    request: TranscriptSearchRequest,
    db: DbDep,
    settings: SettingsDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    skip: Annotated[int, Query(ge=0)] = 0,
):
    try:
        available_topics = await repository.list_topics(db)
    except Exception as err:
        raise HTTPException(status_code=503, detail="Storage unavailable") from err

    try:
        matched_topics = await services.interpret_query(
            request.query, available_topics, settings
        )
    except anthropic.AuthenticationError as err:
        raise HTTPException(
            status_code=500, detail="Service configuration error"
        ) from err
    except (anthropic.APIStatusError, anthropic.APIConnectionError) as err:
        raise HTTPException(status_code=502, detail="Upstream API error") from err
    except ValueError as err:
        raise HTTPException(
            status_code=500, detail="Unexpected response from LLM"
        ) from err

    if not matched_topics:
        return []

    try:
        return await repository.search_by_topics(
            db, matched_topics, skip=skip, limit=limit
        )
    except Exception as err:
        raise HTTPException(status_code=503, detail="Storage unavailable") from err


@router.get("/", response_model=list[TranscriptSummary])
async def list_transcripts(
    db: DbDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    skip: Annotated[int, Query(ge=0)] = 0,
    topic: Annotated[str | None, Query()] = None,
):
    try:
        return await repository.list_transcripts(
            db, skip=skip, limit=limit, topic=topic
        )
    except Exception as err:
        raise HTTPException(status_code=503, detail="Storage unavailable") from err


@router.get("/{id}", response_model=TranscriptDocument)
async def get_transcript(id: str, db: DbDep):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid transcript ID format")
    try:
        doc = await repository.get_transcript_by_id(db, id)
    except Exception as err:
        raise HTTPException(status_code=503, detail="Storage unavailable") from err
    if doc is None:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return doc
