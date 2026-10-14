"""Read-only HTTP smoke with fictional account. Prints counts, never credentials."""
import json
from pathlib import Path
import httpx

root = Path(__file__).resolve().parents[1]
access = (root / '.local/demo-access.txt').read_text(encoding='utf-8')
password = access.split('Contraseña de demostración: ',1)[1].strip()
base = 'http://127.0.0.1:8000/api'
with httpx.Client(base_url=base, timeout=20) as client:
    response = client.post('/auth/login', json={'email':'admin@example.invalid','password':password})
    response.raise_for_status()
    client.headers['X-CSRF-Token'] = response.json()['csrf_token']
    fixture = {}
    for key in ('meta','lookups','dashboard','alerts'):
        response = client.get('/'+key);response.raise_for_status();fixture[key]=response.json()
    for name in fixture['meta']:
        response = client.get('/'+name);response.raise_for_status();fixture[name]=response.json()
    for name in ('tasks','documents','agreements','deliverables','indicator-results','audit'):
        response = client.get('/reports/'+name+'.csv');response.raise_for_status()
        assert response.text.startswith('\ufeff')
    client.post('/auth/logout').raise_for_status()
    assert client.get('/tasks').status_code == 401
destination = root / '.local/qa/api-contract.json'
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(fixture, ensure_ascii=False, indent=2), encoding='utf-8')
print(f"HTTP correcto: {len(fixture['meta'])} recursos; 6 exportaciones CSV; cierre de sesión y 401 verificados.")
