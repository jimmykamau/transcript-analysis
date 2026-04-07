from typing import Annotated

import anthropic
from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings
from app.dependencies import get_settings
from app.transcripts import services
from app.transcripts.models import TranscriptAnalysis, TranscriptRequest

router = APIRouter()

SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.get("/")
async def root():
    return {"status": "ok"}


@router.post("/analyze", response_model=TranscriptAnalysis)
async def analyze(request: TranscriptRequest, settings: SettingsDep):
    try:
        return await services.analyze_transcript(request.transcript, settings)
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
