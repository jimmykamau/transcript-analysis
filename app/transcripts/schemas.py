from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.transcripts.models import TranscriptAnalysis


class TranscriptRequest(BaseModel):
    transcript: Annotated[str, Field(min_length=1)]


class AnalyzeResponse(TranscriptAnalysis):
    id: str
    created_at: datetime


class TranscriptSummary(BaseModel):
    id: str
    qa_score: Annotated[int, Field(ge=1, le=10)]
    sentiment: Literal["positive", "neutral", "negative"]
    summary: str
    created_at: datetime
    topics: list[str] = []


class TranscriptSearchRequest(BaseModel):
    query: Annotated[str, Field(min_length=1)]
