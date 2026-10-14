"""Restore wheel archives from the read-only pip HTTP cache into workspace."""
from pathlib import Path
import zipfile
import shutil
import email

cache = Path.home() / 'AppData/Local/pip/Cache/http-v2'
destination = Path('.local/wheels')
destination.mkdir(parents=True, exist_ok=True)
for path in cache.rglob('*.body'):
    if not zipfile.is_zipfile(path):
        continue
    with zipfile.ZipFile(path) as wheel:
        metadata = next((n for n in wheel.namelist() if n.endswith('.dist-info/METADATA')), None)
        if not metadata:
            continue
        info = email.message_from_bytes(wheel.read(metadata))
        wheel_info = email.message_from_bytes(wheel.read(metadata.replace('METADATA', 'WHEEL')))
        tags = wheel_info.get_all('Tag')
        tag = tags[-1]
        name = info['Name'].replace('-', '_')
        filename = f"{name}-{info['Version']}-{tag}.whl"
        shutil.copyfile(path, destination / filename)
        print(filename)
