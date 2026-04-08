from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import anthropic
import pytest

from app.transcripts import services
from app.transcripts.models import TranscriptDocument


@pytest.fixture(autouse=True)
def clear_client_cache():
    services._get_client.cache_clear()
    yield
    services._get_client.cache_clear()


_SAVED = TranscriptDocument(
    id="507f1f77bcf86cd799439011",
    transcript="Agent: Hello. Customer: Hi, I need help.",
    qa_score=8,
    qa_justification="The agent resolved the issue promptly.",
    summary="Customer contacted support about a password reset. Agent resolved it quickly.",
    sentiment="positive",
    created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
)

_SAVED_WITH_TOPICS = TranscriptDocument(
    id="507f1f77bcf86cd799439011",
    transcript="Agent: Hello. Customer: Hi.",
    qa_score=8,
    qa_justification="The agent resolved the issue promptly.",
    summary="Customer contacted support about a password reset.",
    sentiment="positive",
    created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
    topics=["password_reset"],
)


@pytest.mark.anyio
async def test_analyze_transcript_success(client):
    mock_block = MagicMock()
    mock_block.type = "tool_use"
    mock_block.name = "analyze_transcript"
    mock_block.input = {
        "qa_score": 8,
        "qa_justification": "The agent resolved the issue promptly.",
        "summary": "Customer contacted support about a password reset. Agent resolved it quickly.",
        "sentiment": "positive",
    }

    mock_response = MagicMock()
    mock_response.content = [mock_block]

    mock_instance = AsyncMock()
    mock_instance.messages.create = AsyncMock(return_value=mock_response)

    with (
        patch(
            "app.transcripts.services.anthropic.AsyncAnthropic",
            return_value=mock_instance,
        ),
        patch(
            "app.transcripts.router.repository.save_transcript",
            new=AsyncMock(return_value=_SAVED),
        ),
    ):
        response = await client.post(
            "/transcripts/analyze",
            json={"transcript": "Agent: Hello. Customer: Hi, I need help."},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["qa_score"] == 8
    assert data["sentiment"] == "positive"
    assert "qa_justification" in data
    assert "summary" in data
    assert data["id"] == "507f1f77bcf86cd799439011"
    assert "created_at" in data


@pytest.mark.anyio
async def test_analyze_transcript_includes_topics(client):
    mock_block = MagicMock()
    mock_block.type = "tool_use"
    mock_block.name = "analyze_transcript"
    mock_block.input = {
        "qa_score": 8,
        "qa_justification": "The agent resolved the issue promptly.",
        "summary": "Customer contacted support about a password reset.",
        "sentiment": "positive",
        "topics": ["password_reset"],
    }

    mock_response = MagicMock()
    mock_response.content = [mock_block]

    mock_instance = AsyncMock()
    mock_instance.messages.create = AsyncMock(return_value=mock_response)

    with (
        patch(
            "app.transcripts.services.anthropic.AsyncAnthropic",
            return_value=mock_instance,
        ),
        patch(
            "app.transcripts.router.repository.save_transcript",
            new=AsyncMock(return_value=_SAVED_WITH_TOPICS),
        ),
    ):
        response = await client.post(
            "/transcripts/analyze",
            json={"transcript": "Agent: Hello. Customer: Hi."},
        )

    assert response.status_code == 200
    assert response.json()["topics"] == ["password_reset"]


@pytest.mark.anyio
async def test_analyze_transcript_empty_transcript(client):
    response = await client.post("/transcripts/analyze", json={"transcript": ""})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_analyze_transcript_api_failure(client):
    mock_instance = AsyncMock()
    mock_instance.messages.create.side_effect = anthropic.APIStatusError(
        "rate limited",
        response=MagicMock(status_code=429, headers={}),
        body={},
    )

    with patch(
        "app.transcripts.services.anthropic.AsyncAnthropic", return_value=mock_instance
    ):
        response = await client.post(
            "/transcripts/analyze",
            json={"transcript": "Agent: Hello. Customer: Hi."},
        )

    assert response.status_code == 502
    assert response.json()["detail"] == "Upstream API error"


@pytest.mark.anyio
async def test_analyze_transcript_storage_failure(client):
    mock_block = MagicMock()
    mock_block.type = "tool_use"
    mock_block.name = "analyze_transcript"
    mock_block.input = {
        "qa_score": 7,
        "qa_justification": "Acceptable handling.",
        "summary": "Short call.",
        "sentiment": "neutral",
    }

    mock_response = MagicMock()
    mock_response.content = [mock_block]

    mock_instance = AsyncMock()
    mock_instance.messages.create = AsyncMock(return_value=mock_response)

    with (
        patch(
            "app.transcripts.services.anthropic.AsyncAnthropic",
            return_value=mock_instance,
        ),
        patch(
            "app.transcripts.router.repository.save_transcript",
            new=AsyncMock(side_effect=Exception("connection refused")),
        ),
    ):
        response = await client.post(
            "/transcripts/analyze",
            json={"transcript": "Agent: Hello."},
        )

    assert response.status_code == 503
    assert response.json()["detail"] == "Storage unavailable"
