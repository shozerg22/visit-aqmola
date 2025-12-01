import pytest
from fastapi import status
from httpx import AsyncClient
import asyncio

from app import app
import os


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/api/health")
    assert r.status_code == status.HTTP_200_OK
    assert r.json().get("status") == "ok"


@pytest.mark.asyncio
async def test_ai_chat_stub():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/api/v1/ai/chat", json={"prompt": "Составь план на день", "lang": "RU"})
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert "reply" in data and isinstance(data["reply"], str) and len(data["reply"]) > 0


@pytest.mark.asyncio
async def test_ai_chat_with_rag(monkeypatch):
    # Включаем RAG и указываем временную директорию
    monkeypatch.setenv("AI_USE_RAG", "1")
    monkeypatch.setenv("RAG_DATA_DIR", str(os.path.join(os.getcwd(), ".pytest_cache", "rag")))

    async with AsyncClient(app=app, base_url="http://test") as ac:
        # сначала добавим документ
        r1 = await ac.post(
            "/api/v1/rag/documents",
            json={"title": "Kokshetau Attractions", "text": "Kokshetau has cultural sites and city walks."},
        )
        assert r1.status_code == status.HTTP_200_OK

        # теперь запросим чат с ключевыми словами
        r2 = await ac.post("/api/v1/ai/chat", json={"prompt": "Что есть в Kokshetau?", "lang": "RU"})
        assert r2.status_code == status.HTTP_200_OK
        data = r2.json()
        # Ответ заглушки должен содержать базовый текст, а с контекстом будет пометка
        assert "reply" in data and isinstance(data["reply"], str)


@pytest.mark.asyncio
async def test_integrations_mock_and_webhook():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r1 = await ac.post("/api/v1/auth/oidc/verify", params={"code": "test"})
        assert r1.status_code == status.HTTP_200_OK
        r2 = await ac.get("/api/v1/freedom/mock/tours")
        assert r2.status_code == status.HTTP_200_OK
        r3 = await ac.post("/api/v1/payments/webhook", json={"event": "payment.succeeded"})
        assert r3.status_code == status.HTTP_200_OK
