from functools import lru_cache

import anthropic
from pydantic import ValidationError

from app.config import Settings
from app.transcripts.schemas import TranscriptAnalysis

_TOOL = {
    "name": "analyze_transcript",
    "description": "Analyze a call center transcript and return QA metrics.",
    "input_schema": TranscriptAnalysis.model_json_schema(),
}

_SYSTEM = (
    "You are a QA analyst evaluating customer service call transcripts. "
    "Call the `analyze_transcript` tool with a score (1–10), a one-sentence "
    "justification, a 2–3 sentence summary, and the customer's overall sentiment."
)


@lru_cache
def _get_client(api_key: str) -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=api_key, max_retries=3)


async def analyze_transcript(transcript: str, settings: Settings) -> TranscriptAnalysis:
    client = _get_client(settings.anthropic_api_key)
    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=settings.claude_max_tokens,
        system=_SYSTEM,
        tools=[_TOOL],
        tool_choice={"type": "tool", "name": _TOOL["name"]},
        messages=[{"role": "user", "content": transcript}],
    )
    block = next(
        (
            b
            for b in response.content
            if b.type == "tool_use" and b.name == _TOOL["name"]
        ),
        None,
    )
    if block is None:
        raise ValueError("Unexpected response from LLM")
    try:
        return TranscriptAnalysis(**block.input)
    except ValidationError as err:
        raise ValueError("Unexpected response from LLM") from err
