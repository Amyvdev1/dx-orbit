from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_invalid_structure_returns_actionable_client_error():
    malformed={'openapi':'3.1.0','paths':['invalid']}
    for endpoint in ('/api/analyze','/api/report/markdown'):
        response=client.post(endpoint,json=malformed)
        assert response.status_code==422
        assert 'structure' in response.json()['detail']
    assert client.post('/api/compare',json={'before':malformed,'after':{}}).status_code==422
    assert client.post('/api/analyze-file',files={'file':('api.json','{"paths":["invalid"]}','application/json')}).status_code==422

def test_upload_size_is_bounded():
    assert client.post('/api/analyze-file',files={'file':('large.json',b' '*2_000_001,'application/json')}).status_code==413

def test_health_and_analyze():
    assert client.get('/health').json()['status']=='ok'
    r=client.post('/api/analyze',json={"openapi":"3.1.0","info":{"title":"T","version":"1"},"paths":{}})
    assert r.status_code==200 and 'dx_score' in r.json()

def test_markdown_endpoint():
    r=client.post('/api/report/markdown',json={"openapi":"3.1.0","info":{"title":"T","version":"1"},"paths":{}})
    assert r.status_code==200 and r.text.startswith('# DX Orbit Report')
