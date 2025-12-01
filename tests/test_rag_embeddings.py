import os
import pytest
from fastapi.testclient import TestClient
from app import app

@pytest.mark.skipif(not os.getenv('OPENAI_API_KEY'), reason='OPENAI_API_KEY not set')
def test_rag_embeddings_search():
    os.environ['DISABLE_DB_INIT'] = '1'
    os.environ['RAG_SEARCH_MODE'] = 'embeddings'
    client = TestClient(app)
    # Ingest few docs
    docs = [
        {"title": "Burabay Lake", "text": "Beautiful lake in Aqmola region with pine forests."},
        {"title": "Kokshetau City", "text": "City in Akmola with historical places and museums."},
        {"title": "Aqmola Cuisine", "text": "Traditional Kazakh meals and local cuisine specialties."},
    ]
    r = client.post('/api/v1/rag/documents/batch', json={"items": docs})
    assert r.status_code == 200, r.text
    # Query for lakes
    r2 = client.get('/api/v1/rag/search', params={'q': 'lake with forests', 'k': 2})
    assert r2.status_code == 200, r2.text
    data = r2.json()
    assert len(data.get('results', [])) >= 1
