import pytest
from httpx import AsyncClient
from fastapi import status

from app import app

@pytest.mark.asyncio
async def test_rag_batch_documents():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/api/v1/rag/documents/batch", json={
            "items": [
                {"title": "Burabay Guide", "text": "Burabay National Park...", "lang": "EN"},
                {"title": "Kokshetau Walks", "text": "City walks and museums", "lang": "EN"}
            ]
        })
        assert r.status_code == status.HTTP_200_OK, r.text
        data = r.json()
        assert data.get("ok") == 2
        assert isinstance(data.get("ids"), list)
