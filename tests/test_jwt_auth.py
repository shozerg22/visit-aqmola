import os, jwt
# Настройка тестовой БД до импорта приложения
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///:memory:'
os.environ['DISABLE_DB_INIT'] = '1'
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_jwt_issue_and_admin_access():
    # DISABLE_DB_INIT уже выставлен до импорта
    os.environ['JWT_SECRET'] = 'test-secret'
    os.environ['ADMIN_TOKEN'] = 'adm-token'
    # Создаём пользователя (обычный)
    user_body = {"name": "Alice", "email": "alice@example.com"}
    r = client.post('/api/v1/users', json=user_body)
    assert r.status_code == 200, r.text
    uid = r.json()['id']
    # Выдаём JWT
    r2 = client.post('/api/v1/auth/jwt/issue', params={'user_id': uid})
    assert r2.status_code == 200, r2.text
    token = r2.json()['access_token']
    # Попытка вызвать админ эндпоинт без админ роли -> 403
    r3 = client.get('/api/v1/admin/complaints', headers={'Authorization': f'Bearer {token}'})
    assert r3.status_code == 403
    # Создаём админа
    admin_body = {"name": "Root", "email": "root@example.com", "role": "admin"}
    r4 = client.post('/api/v1/users', json=admin_body)
    assert r4.status_code == 200, r4.text
    admin_id = r4.json()['id']
    r5 = client.post('/api/v1/auth/jwt/issue', params={'user_id': admin_id})
    assert r5.status_code == 200
    admin_token = r5.json()['access_token']
    # Доступ с админ JWT
    r6 = client.get('/api/v1/admin/complaints', headers={'Authorization': f'Bearer {admin_token}'})
    # Может быть пустой список или 200
    assert r6.status_code in (200, 204)

def test_jwt_issue_by_email():
    # DISABLE_DB_INIT уже выставлен до импорта
    os.environ['JWT_SECRET'] = 'test-secret'
    user_body = {"name": "Bob", "email": "bob@example.com"}
    r = client.post('/api/v1/users', json=user_body)
    assert r.status_code == 200
    r2 = client.post('/api/v1/auth/jwt/issue', params={'email': 'bob@example.com'})
    assert r2.status_code == 200
    data = r2.json()
    assert data['role'] == 'user'
