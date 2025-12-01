import os
import pytest
from httpx import AsyncClient
from fastapi import status

from app import app

@pytest.mark.asyncio
async def test_bookings_complaints_events(monkeypatch):
    db_url = os.getenv('DATABASE_URL')
    assert db_url and db_url.startswith('postgresql+asyncpg'), 'DATABASE_URL must be set to asyncpg URL'

    async with AsyncClient(app=app, base_url="http://test") as ac:
        # user
        r_user = await ac.post('/api/v1/users', json={'name': 'User2', 'email': 'u2@example.com'})
        assert r_user.status_code == status.HTTP_200_OK
        uid = r_user.json()['id']

        # object
        r_obj = await ac.post('/api/v1/objects', json={'name': 'Kokshetau Museum', 'description': 'Culture', 'lat': 53.28, 'lon': 69.39})
        assert r_obj.status_code == status.HTTP_200_OK
        oid = r_obj.json()['id']

        # booking
        r_book = await ac.post('/api/v1/bookings', json={'user_id': uid, 'object_id': oid, 'start_date': '2025-01-01', 'end_date': '2025-01-03'})
        assert r_book.status_code == status.HTTP_200_OK
        booking = r_book.json()
        assert booking['status']

        # complaint
        r_comp = await ac.post('/api/v1/complaints', json={'user_id': uid, 'object_id': oid, 'category': 'service', 'text': 'Issue found', 'lat': 53.28, 'lon': 69.39})
        assert r_comp.status_code == status.HTTP_200_OK
        comp_id = r_comp.json()['id']

        # events
        r_event = await ac.post('/api/v1/events', json={'title': 'City Walk', 'description': 'Guided tour', 'lat': 53.28, 'lon': 69.39})
        assert r_event.status_code == status.HTTP_200_OK

        # list
        r_events = await ac.get('/api/v1/events')
        assert r_events.status_code == status.HTTP_200_OK
        assert isinstance(r_events.json(), list)

        # admin status update for complaint (should require header)
        r_status_fail = await ac.post(f'/api/v1/complaints/{comp_id}/status', json={'status': 'in_review'})
        assert r_status_fail.status_code == status.HTTP_401_UNAUTHORIZED

        r_status_ok = await ac.post(
            f'/api/v1/complaints/{comp_id}/status',
            json={'status': 'in_review'},
            headers={'X-Admin-Token': os.getenv('ADMIN_TOKEN', 'changeme')}
        )
        assert r_status_ok.status_code == status.HTTP_200_OK
