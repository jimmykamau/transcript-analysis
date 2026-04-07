from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

_SUMMARIES = [
    {
        "id": "507f1f77bcf86cd799439011",
        "qa_score": 8,
        "sentiment": "positive",
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
    mock.assert_awaited_once_with(mock.call_args[0][0], skip=10, limit=5)


@pytest.mark.anyio
async def test_list_transcripts_invalid_limit(client):
    response = await client.get("/transcripts/?limit=0")
    assert response.status_code == 422

    response = await client.get("/transcripts/?limit=101")
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
