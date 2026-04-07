import pytest


@pytest.mark.anyio
async def test_root(client):
    response = await client.get("/transcripts/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
