import os
from fastapi.testclient import TestClient
from app import app

os.environ['DISABLE_DB_INIT'] = '1'
os.environ['MAX_RAG_DOC_CHARS'] = '10'
os.environ['JWT_SECRET'] = 'test-secret'

client = TestClient(app)

def _issue_cm_token():
    # content-manager user
    r = client.post('/api/v1/users', json={'name':'CM','email':'cm@example.com','role':'content-manager'})
    uid = r.json()['id']
    t = client.post(f'/api/v1/auth/jwt/issue?user_id={uid}').json()['access_token']
    return t

def test_rag_document_size_limit():
    token = _issue_cm_token()
    headers = {'Authorization': f'Bearer {token}'}
    # допустимый
    ok = client.post('/api/v1/rag/documents', json={'title':'A','text':'1234567890','tags':['t']}, headers=headers)
    assert ok.status_code == 200
    # превышение
    too_big = client.post('/api/v1/rag/documents', json={'title':'B','text':'12345678901','tags':['t']}, headers=headers)
    assert too_big.status_code == 400
