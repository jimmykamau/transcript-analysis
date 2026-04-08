from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class TranscriptAnalysis(BaseModel):
    qa_score: Annotated[int, Field(ge=1, le=10)]
    qa_justification: str
    summary: str
    sentiment: Literal["positive", "neutral", "negative"]
    topics: list[str] = Field(default_factory=list)


class TranscriptDocument(TranscriptAnalysis):
    id: str
    transcript: str
    created_at: datetime
