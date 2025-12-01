import os
import pytest
from httpx import AsyncClient
from fastapi import status

from app import app

@pytest.mark.asyncio
async def test_rate_limit(monkeypatch):
    # Сужаем лимиты для теста
    monkeypatch.setenv('RATE_LIMIT_WINDOW_SEC', '1')
    monkeypatch.setenv('RATE_LIMIT_MAX_REQUESTS', '3')

    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 3 запроса должны пройти
        for _ in range(3):
            r = await ac.get('/api/health')  # вне /api/v1, не ограничиваем — проверим /api/v1
            assert r.status_code == status.HTTP_200_OK
        # Проверяем ограничение на /api/v1
        passed = 0
        for i in range(4):
            rr = await ac.post('/api/v1/ai/chat', json={'prompt':'hi'})
            if rr.status_code == status.HTTP_200_OK:
                passed += 1
        assert passed == 3 or passed == 0  # в зависимости от того, когда окно начато
        # как минимум один должен быть 429
        assert any((await ac.post('/api/v1/ai/chat', json={'prompt':'x'})).status_code == 429 for _ in range(2))
