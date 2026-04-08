from functools import lru_cache

import anthropic
from pydantic import ValidationError

from app.config import Settings
from app.transcripts.models import TranscriptAnalysis

_TOOL = {
    "name": "analyze_transcript",
    "description": "Analyze a call center transcript and return QA metrics.",
    "input_schema": TranscriptAnalysis.model_json_schema(),
}

_SYSTEM = (
    "You are a QA analyst evaluating customer service call transcripts. "
    "Call the `analyze_transcript` tool with a score (1–10), a one-sentence "
    "justification, a 2–3 sentence summary, the customer's overall sentiment, "
    "and a list of short lowercase topic slugs (e.g. apology, billing, escalation, "
    "password_reset, pricing, refund, technical_issue, wait_time) identifying key themes."
)

_SEARCH_TOOL = {
    "name": "map_topics",
    "description": "Select topic slugs from the available list that match the natural-language query.",
    "input_schema": {
        "type": "object",
        "properties": {
            "topics": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Matching topic slugs chosen only from the available list",
            }
        },
        "required": ["topics"],
    },
}


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


async def interpret_query(
    query: str, available_topics: list[str], settings: Settings
) -> list[str]:
    if not available_topics:
        return []
    client = _get_client(settings.anthropic_api_key)
    system = (
        f"You map natural-language queries to topic slugs. "
        f"Available topics: {', '.join(available_topics)}. "
        f"Pick only slugs from this list that match the query. "
        f"Call the map_topics tool."
    )
    response = await client.messages.create(
        model=settings.claude_search_model,
        max_tokens=256,
        system=system,
        tools=[_SEARCH_TOOL],
        tool_choice={"type": "tool", "name": _SEARCH_TOOL["name"]},
        messages=[{"role": "user", "content": query}],
    )
    block = next(
        (
            b
            for b in response.content
            if b.type == "tool_use" and b.name == _SEARCH_TOOL["name"]
        ),
        None,
    )
    if block is None:
        return []
    topics = block.input.get("topics", [])
    return [t for t in topics if t in available_topics]
