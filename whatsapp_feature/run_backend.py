"""Alternative entry point: opt-in extension, no edits to the original backend.

Run with a Python environment containing the original backend requirements.
Runtime data is isolated under this new folder by default.
"""
import argparse
import os
from pathlib import Path
import sys


def create_app(runtime_root=None):
    sys.dont_write_bytecode = True
    root = Path(__file__).resolve().parent
    runtime = Path(runtime_root) if runtime_root else root / 'runtime'
    os.environ['NEXA_DATA_DIR'] = str(runtime / 'backend-data')
    os.environ['NEXA_MODELS_DIR'] = str(runtime / 'models')
    os.environ['NEXA_ENV_FILE'] = str(runtime / '.env')
    os.environ['SQLITE_DB_PATH'] = str(runtime / 'backend-data' / 'nexaai.sqlite3')
    sys.path.insert(0, str(root.parent / 'backend'))
    from app.main import app
    from .adapter import install
    sender, pool = install(runtime / 'whatsapp-state')

    @app.get('/api/whatsapp-extension/health')
    def health():
        return {'extension': 'whatsapp-text-send', 'enabled_in_this_process': True,
                'live_delivery_verified': False, 'original_source_modified': False,
                'note': 'Enable WhatsApp Web Sending in Security Center. Runtime data is isolated.'}

    @app.get('/whatsapp-extension', include_in_schema=False)
    def guide():
        from fastapi.responses import FileResponse
        return FileResponse(root / 'status.html')

    return app, sender, pool


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    app, sender, pool = create_app()
    import uvicorn
    try:
        uvicorn.run(app, host='127.0.0.1', port=args.port)
    finally:
        pool.shutdown()


if __name__ == '__main__':
    main()
