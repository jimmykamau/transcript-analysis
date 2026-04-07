from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class TranscriptDocument(BaseModel):
    id: str
    transcript: str
    qa_score: Annotated[int, Field(ge=1, le=10)]
    qa_justification: str
    summary: str
    sentiment: Literal["positive", "neutral", "negative"]
    created_at: datetime
