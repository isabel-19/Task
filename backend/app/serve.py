"""Container entry point. Migrations and initial account creation are explicit steps."""
import os
import uvicorn


if __name__ == '__main__':
    from .deploy import prepare
    prepare()
    uvicorn.run('app.main:app', host='0.0.0.0', port=int(os.environ.get('PORT', '10000')))
