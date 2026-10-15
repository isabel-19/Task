"""Serve the compiled Vue app alongside the API, without exposing private storage."""
from pathlib import Path
from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles


class FrontendFiles(StaticFiles):
    async def get_response(self, path, scope):
        path = path.replace('\\', '/').lstrip('/')
        # An unknown API URL must never return the SPA login document.
        if path == 'api' or path.startswith('api/'):
            raise HTTPException(404)
        try:
            return await super().get_response(path, scope)
        except HTTPException as error:
            if error.status_code != 404 or scope['method'] not in ('GET', 'HEAD'):
                raise
            if any(part.startswith('.') for part in Path(path).parts) or '.' in Path(path).name:
                raise
            return await super().get_response('index.html', scope)


def mount_frontend(app, directory):
    if not directory:
        return
    root = Path(directory).resolve(strict=True)
    if not (root / 'index.html').is_file():
        raise RuntimeError('FRONTEND_DIST debe apuntar a la interfaz compilada.')
    app.mount('/', FrontendFiles(directory=root, html=True), name='frontend')
