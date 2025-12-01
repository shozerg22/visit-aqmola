import os
import pytest
from httpx import AsyncClient
from fastapi import status

from app import app


@pytest.mark.asyncio
async def test_rag_ingest_and_search(tmp_path, monkeypatch):
    # Изолируем стор в temp-директории
    monkeypatch.setenv("RAG_DATA_DIR", str(tmp_path / "rag"))

    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Ингест документа
        r1 = await ac.post(
            "/api/v1/rag/documents",
            json={
                "title": "Burabay Guide",
                "text": "Burabay National Park is a scenic area with lakes and forests in Aqmola.",
                "lang": "EN",
                "tags": ["park", "nature"],
            },
        )
        assert r1.status_code == status.HTTP_200_OK, r1.text
        doc = r1.json()
        assert doc.get("ok") is True
        assert "id" in doc and len(doc["id"]) > 0

        # Поиск
        r2 = await ac.get("/api/v1/rag/search", params={"q": "Burabay lakes"})
        assert r2.status_code == status.HTTP_200_OK, r2.text
        data = r2.json()
        assert data.get("query") == "Burabay lakes"
        results = data.get("results", [])
        assert isinstance(results, list)
        # Должен быть найден наш документ
        assert any("Burabay" in (item.get("title") or "") for item in results)
