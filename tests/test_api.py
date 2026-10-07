from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_health_and_analyze():
    assert client.get('/health').json()['status']=='ok'
    r=client.post('/api/analyze',json={"openapi":"3.1.0","info":{"title":"T","version":"1"},"paths":{}})
    assert r.status_code==200 and 'dx_score' in r.json()

def test_markdown_endpoint():
    r=client.post('/api/report/markdown',json={"openapi":"3.1.0","info":{"title":"T","version":"1"},"paths":{}})
    assert r.status_code==200 and r.text.startswith('# DX Orbit Report')
