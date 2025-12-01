import os
import pytest
from httpx import AsyncClient
from fastapi import status

from app import app

@pytest.mark.asyncio
async def test_crud_objects_users_reviews_with_db(monkeypatch):
    # В CI эта переменная будет указывать на Postgres
    db_url = os.getenv('DATABASE_URL')
    assert db_url and db_url.startswith('postgresql+asyncpg'), 'DATABASE_URL must be set to asyncpg URL'

    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Создаём пользователя
        r_user = await ac.post('/api/v1/users', json={
            'external_id': None,
            'name': 'Tester',
            'email': 'tester@example.com'
        })
        assert r_user.status_code == status.HTTP_200_OK, r_user.text
        user = r_user.json(); uid = user['id']

        # Создаём объект
        r_obj = await ac.post('/api/v1/objects', json={
            'name': 'Burabay Lake',
            'description': 'Beautiful lake in Aqmola',
            'lat': 53.1,
            'lon': 69.4
        })
        assert r_obj.status_code == status.HTTP_200_OK, r_obj.text
        obj = r_obj.json(); oid = obj['id']

        # Создаём отзыв
        r_rev = await ac.post('/api/v1/reviews', json={
            'user_id': uid,
            'object_id': oid,
            'rating': 5,
            'text': 'Amazing!'
        })
        assert r_rev.status_code == status.HTTP_200_OK, r_rev.text

        # Читаем объект и проверяем поля
        r_get = await ac.get('/api/v1/objects')
        assert r_get.status_code == status.HTTP_200_OK
        objs = r_get.json()
        assert any(o['id'] == oid for o in objs)

        # Скоринг
        r_score = await ac.get(f'/api/v1/objects/{oid}/score')
        assert r_score.status_code == status.HTTP_200_OK
        data = r_score.json()
        assert data['object_id'] == oid
        assert isinstance(data['avg_rating'], float)
