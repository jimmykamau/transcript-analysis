from typing import Annotated, Literal

from pydantic import BaseModel, Field


class TranscriptRequest(BaseModel):
    transcript: Annotated[str, Field(min_length=1)]


class TranscriptAnalysis(BaseModel):
    qa_score: Annotated[int, Field(ge=1, le=10)]
    qa_justification: str
    summary: str
    sentiment: Literal["positive", "neutral", "negative"]
