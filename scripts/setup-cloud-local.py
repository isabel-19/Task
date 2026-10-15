"""Prepare a local encryption key without printing or replacing existing secrets."""
from pathlib import Path
from cryptography.fernet import Fernet
from dotenv import dotenv_values

root = Path(__file__).resolve().parents[1]
path = root / 'backend/.env'
values = dotenv_values(path) if path.exists() else {}
key = values.get('CLOUD_TOKEN_KEY')
if key:
    Fernet(key.encode())
    print('Se conserva la clave de cifrado local existente.')
else:
    content = path.read_text(encoding='utf-8') if path.exists() else ''
    with path.open('a', encoding='utf-8') as output:
        output.write(('\n' if content and not content.endswith('\n') else '') + 'CLOUD_TOKEN_KEY=' + Fernet.generate_key().decode() + '\n')
    print('Clave de cifrado local preparada en backend/.env; no se muestra en pantalla.')
print('Configura las aplicaciones OAuth de Google/Microsoft y sus redirecciones antes de conectar cuentas reales.')
