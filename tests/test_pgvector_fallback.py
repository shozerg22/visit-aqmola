import os
from fastapi.testclient import TestClient
from app import app

# Имитируем настройку на pgvector без PostgreSQL
os.environ['DISABLE_DB_INIT'] = '1'
os.environ['RAG_BACKEND'] = 'pgvector'
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./test.db'  # не postgres

client = TestClient(app)

def test_pgvector_fallback_to_files():
    # Добавляем документ через контент-менеджера
    r_user = client.post('/api/v1/users', json={'name':'CM','email':'cm2@example.com','role':'content-manager'})
    uid = r_user.json()['id']
    tok = client.post(f'/api/v1/auth/jwt/issue?user_id={uid}').json()['access_token']
    headers={'Authorization': f'Bearer {tok}'}
    add = client.post('/api/v1/rag/documents', json={'title':'X','text':'alpha beta gamma','tags':['t']}, headers=headers)
    assert add.status_code == 200
    # Поиск embeddings (принудительно) должен выполниться на файловом store (mode может откатиться)
    srch = client.get('/api/v1/rag/search', params={'q':'alpha','mode':'embeddings'})
    assert srch.status_code == 200
    data = srch.json()
    # backend откатился — файл store доступен, results есть
    assert 'results' in data
    assert len(data['results']) >= 1
