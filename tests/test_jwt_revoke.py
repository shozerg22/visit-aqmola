import os
import pytest
from fastapi.testclient import TestClient
from app import app

os.environ['DISABLE_DB_INIT'] = '1'
os.environ['JWT_SECRET'] = 'test-secret'

client = TestClient(app)

@pytest.mark.asyncio
async def test_jwt_revoke_access_denied():
    # Создаём пользователя
    resp = client.post('/api/v1/users', json={'name':'Admin','email':'a@example.com','role':'admin'})
    assert resp.status_code == 200
    uid = resp.json()['id']
    # Issue token
    tok_resp = client.post(f'/api/v1/auth/jwt/issue?user_id={uid}')
    assert tok_resp.status_code == 200
    token = tok_resp.json()['access_token']
    # Доступ до ревокации (admin список жалоб)
    ok1 = client.get('/api/v1/admin/complaints', headers={'Authorization': f'Bearer {token}'})
    assert ok1.status_code in (200, 204)
    # Revoke
    rev = client.post('/api/v1/auth/jwt/revoke', params={'token': token})
    assert rev.status_code == 200
    # Повторный доступ должен дать 401 (Token revoked)
    denied = client.get('/api/v1/admin/complaints', headers={'Authorization': f'Bearer {token}'})
    assert denied.status_code == 401
