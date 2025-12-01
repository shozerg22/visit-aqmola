import os
import pytest
from httpx import AsyncClient
from fastapi import status

from app import app

@pytest.mark.asyncio
async def test_rag_search_modes_difference(tmp_path, monkeypatch):
    # Изолируем стор
    monkeypatch.setenv("RAG_DATA_DIR", str(tmp_path / "rag"))
    # Ингест нескольких документов
    docs = [
        {"title": "Burabay Lake", "text": "Beautiful lake with pine forests and clear water in Aqmola."},
        {"title": "Aqmola Forests", "text": "Forests in the Aqmola region near Burabay with rich flora."},
        {"title": "Urban Kokshetau", "text": "City life, museums and urban development."},
    ]
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r_batch = await ac.post("/api/v1/rag/documents/batch", json={"items": docs})
        assert r_batch.status_code == status.HTTP_200_OK, r_batch.text
        # simple mode search
        r_simple = await ac.get("/api/v1/rag/search", params={"q": "burabay forests", "mode": "simple", "k": 3})
        assert r_simple.status_code == status.HTTP_200_OK, r_simple.text
        d_simple = r_simple.json()
        assert d_simple.get("mode") == "simple"
        simple_scores = [res.get("score") for res in d_simple.get("results", [])]
        # tfidf mode search
        r_tfidf = await ac.get("/api/v1/rag/search", params={"q": "burabay forests", "mode": "tfidf", "k": 3})
        assert r_tfidf.status_code == status.HTTP_200_OK, r_tfidf.text
        d_tfidf = r_tfidf.json()
        assert d_tfidf.get("mode") == "tfidf"
        tfidf_scores = [res.get("score") for res in d_tfidf.get("results", [])]
        # Простая проверка: тип скоринга отличается (simple -> целые, tfidf -> float с точностью)
        if simple_scores and tfidf_scores:
            # В simple все score целые (длина пересечения токенов)
            assert all(isinstance(s, int) for s in simple_scores)
            # В tfidf как минимум один score должен быть нецелым (float)
            assert any(isinstance(s, float) and not float(s).is_integer() for s in tfidf_scores)
        # Также проверим, что порядок может отличаться (не жесткое требование)
        if len(d_simple.get("results", [])) >= 2 and len(d_tfidf.get("results", [])) >= 2:
            titles_simple = [res.get("title") for res in d_simple.get("results", [])]
            titles_tfidf = [res.get("title") for res in d_tfidf.get("results", [])]
            assert titles_simple != titles_tfidf or simple_scores != tfidf_scores
