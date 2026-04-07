from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.transcripts.models import TranscriptDocument


class TranscriptRequest(BaseModel):
    transcript: Annotated[str, Field(min_length=1)]


class TranscriptAnalysis(BaseModel):
    qa_score: Annotated[int, Field(ge=1, le=10)]
    qa_justification: str
    summary: str
    sentiment: Literal["positive", "neutral", "negative"]


class AnalyzeResponse(TranscriptAnalysis):
    id: str
    created_at: datetime


class TranscriptSummary(BaseModel):
    id: str
    qa_score: Annotated[int, Field(ge=1, le=10)]
    sentiment: Literal["positive", "neutral", "negative"]
    created_at: datetime


class TranscriptDetail(TranscriptDocument):
    pass
