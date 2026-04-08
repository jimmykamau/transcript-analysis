from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import anthropic
import pytest

_SUMMARIES = [
    {
        "id": "507f1f77bcf86cd799439011",
        "qa_score": 8,
        "sentiment": "positive",
        "summary": "Customer called about a billing issue. Agent resolved it promptly.",
        "created_at": datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
    }
]

_DETAIL = {
    "id": "507f1f77bcf86cd799439011",
    "transcript": "Agent: Hello. Customer: Hi.",
    "qa_score": 8,
    "qa_justification": "Good handling.",
    "summary": "Quick call.",
    "sentiment": "positive",
    "created_at": datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
}


@pytest.mark.anyio
async def test_list_transcripts(client):
    with patch(
        "app.transcripts.router.repository.list_transcripts",
        new=AsyncMock(return_value=_SUMMARIES),
    ):
        response = await client.get("/transcripts/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == "507f1f77bcf86cd799439011"
    assert data[0]["qa_score"] == 8
    assert data[0]["sentiment"] == "positive"
    assert "created_at" in data[0]


@pytest.mark.anyio
async def test_list_transcripts_pagination(client):
    mock = AsyncMock(return_value=_SUMMARIES)
    with patch("app.transcripts.router.repository.list_transcripts", new=mock):
        await client.get("/transcripts/?limit=5&skip=10")
    mock.assert_awaited_once_with(mock.call_args[0][0], skip=10, limit=5, topic=None)


@pytest.mark.anyio
async def test_list_transcripts_topic_filter(client):
    mock = AsyncMock(return_value=_SUMMARIES)
    with patch("app.transcripts.router.repository.list_transcripts", new=mock):
        await client.get("/transcripts/?topic=apology")
    mock.assert_awaited_once_with(
        mock.call_args[0][0], skip=0, limit=20, topic="apology"
    )


@pytest.mark.anyio
async def test_list_transcripts_no_topic_filter(client):
    mock = AsyncMock(return_value=_SUMMARIES)
    with patch("app.transcripts.router.repository.list_transcripts", new=mock):
        await client.get("/transcripts/")
    mock.assert_awaited_once_with(mock.call_args[0][0], skip=0, limit=20, topic=None)


@pytest.mark.anyio
async def test_list_transcripts_invalid_params(client):
    response = await client.get("/transcripts/?limit=0")
    assert response.status_code == 422

    response = await client.get("/transcripts/?limit=101")
    assert response.status_code == 422

    response = await client.get("/transcripts/?skip=-1")
    assert response.status_code == 422


@pytest.mark.anyio
async def test_list_transcripts_storage_failure(client):
    with patch(
        "app.transcripts.router.repository.list_transcripts",
        new=AsyncMock(side_effect=Exception("db down")),
    ):
        response = await client.get("/transcripts/")

    assert response.status_code == 503
    assert response.json()["detail"] == "Storage unavailable"


@pytest.mark.anyio
async def test_get_transcript_by_id(client):
    with patch(
        "app.transcripts.router.repository.get_transcript_by_id",
        new=AsyncMock(return_value=_DETAIL),
    ):
        response = await client.get("/transcripts/507f1f77bcf86cd799439011")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "507f1f77bcf86cd799439011"
    assert data["transcript"] == "Agent: Hello. Customer: Hi."
    assert data["qa_score"] == 8
    assert "qa_justification" in data
    assert "summary" in data
    assert "created_at" in data


@pytest.mark.anyio
async def test_get_transcript_invalid_id_format(client):
    response = await client.get("/transcripts/not-a-valid-id")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid transcript ID format"


@pytest.mark.anyio
async def test_get_transcript_not_found(client):
    with patch(
        "app.transcripts.router.repository.get_transcript_by_id",
        new=AsyncMock(return_value=None),
    ):
        response = await client.get("/transcripts/507f1f77bcf86cd799439011")

    assert response.status_code == 404
    assert response.json()["detail"] == "Transcript not found"


@pytest.mark.anyio
async def test_get_transcript_storage_failure(client):
    with patch(
        "app.transcripts.router.repository.get_transcript_by_id",
        new=AsyncMock(side_effect=Exception("db down")),
    ):
        response = await client.get("/transcripts/507f1f77bcf86cd799439011")

    assert response.status_code == 503
    assert response.json()["detail"] == "Storage unavailable"


@pytest.mark.anyio
async def test_list_topics(client):
    with patch(
        "app.transcripts.router.repository.list_topics",
        new=AsyncMock(return_value=["apology", "billing"]),
    ):
        response = await client.get("/transcripts/topics")

    assert response.status_code == 200
    assert response.json() == ["apology", "billing"]


@pytest.mark.anyio
async def test_list_topics_storage_failure(client):
    with patch(
        "app.transcripts.router.repository.list_topics",
        new=AsyncMock(side_effect=Exception("db down")),
    ):
        response = await client.get("/transcripts/topics")

    assert response.status_code == 503
    assert response.json()["detail"] == "Storage unavailable"


_SEARCH_SUMMARIES = [
    {
        "id": "507f1f77bcf86cd799439011",
        "qa_score": 7,
        "sentiment": "negative",
        "summary": "Customer called to dispute a charge. Agent apologized for the error and issued a refund.",
        "created_at": datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
        "topics": ["apology", "escalation"],
    }
]


@pytest.mark.anyio
async def test_search_success(client):
    with (
        patch(
            "app.transcripts.router.repository.list_topics",
            new=AsyncMock(return_value=["apology", "billing", "escalation"]),
        ),
        patch(
            "app.transcripts.router.services.interpret_query",
            new=AsyncMock(return_value=["apology"]),
        ),
        patch(
            "app.transcripts.router.repository.search_by_topics",
            new=AsyncMock(return_value=_SEARCH_SUMMARIES),
        ),
    ):
        response = await client.post(
            "/transcripts/search",
            json={"query": "calls where the agent apologized"},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "507f1f77bcf86cd799439011"
    assert data[0]["topics"] == ["apology", "escalation"]


@pytest.mark.anyio
async def test_search_no_match(client):
    with (
        patch(
            "app.transcripts.router.repository.list_topics",
            new=AsyncMock(return_value=["apology"]),
        ),
        patch(
            "app.transcripts.router.services.interpret_query",
            new=AsyncMock(return_value=[]),
        ),
    ):
        response = await client.post(
            "/transcripts/search", json={"query": "calls about flying"}
        )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
async def test_search_empty_query(client):
    response = await client.post("/transcripts/search", json={"query": ""})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_search_list_topics_storage_failure(client):
    with patch(
        "app.transcripts.router.repository.list_topics",
        new=AsyncMock(side_effect=Exception("db down")),
    ):
        response = await client.post(
            "/transcripts/search", json={"query": "apology calls"}
        )
    assert response.status_code == 503
    assert response.json()["detail"] == "Storage unavailable"


@pytest.mark.anyio
async def test_search_interpret_query_api_failure(client):
    with (
        patch(
            "app.transcripts.router.repository.list_topics",
            new=AsyncMock(return_value=["apology"]),
        ),
        patch(
            "app.transcripts.router.services.interpret_query",
            new=AsyncMock(
                side_effect=anthropic.APIStatusError(
                    "rate limited",
                    response=MagicMock(status_code=429, headers={}),
                    body={},
                )
            ),
        ),
    ):
        response = await client.post(
            "/transcripts/search", json={"query": "apology calls"}
        )
    assert response.status_code == 502
    assert response.json()["detail"] == "Upstream API error"


@pytest.mark.anyio
async def test_search_interpret_query_value_error(client):
    with (
        patch(
            "app.transcripts.router.repository.list_topics",
            new=AsyncMock(return_value=["apology"]),
        ),
        patch(
            "app.transcripts.router.services.interpret_query",
            new=AsyncMock(side_effect=ValueError("Unexpected response from LLM")),
        ),
    ):
        response = await client.post(
            "/transcripts/search", json={"query": "apology calls"}
        )
    assert response.status_code == 500
    assert response.json()["detail"] == "Unexpected response from LLM"


@pytest.mark.anyio
async def test_search_search_by_topics_storage_failure(client):
    with (
        patch(
            "app.transcripts.router.repository.list_topics",
            new=AsyncMock(return_value=["apology"]),
        ),
        patch(
            "app.transcripts.router.services.interpret_query",
            new=AsyncMock(return_value=["apology"]),
        ),
        patch(
            "app.transcripts.router.repository.search_by_topics",
            new=AsyncMock(side_effect=Exception("db down")),
        ),
    ):
        response = await client.post(
            "/transcripts/search", json={"query": "apology calls"}
        )
    assert response.status_code == 503
    assert response.json()["detail"] == "Storage unavailable"
