import os
import sys
from pathlib import Path
import uvicorn

if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("NEXA_WHATSAPP_RELIABLE_SENDER", "1")

from app.core.config import get_settings
from app.main import app


def main() -> None:
    settings = get_settings()
    frozen = bool(getattr(sys, "frozen", False))

    uvicorn.run(
        app if frozen else "app.main:app",
        host=settings.backend_host,
        port=int(settings.backend_port),
        reload=settings.app_env == "development" and not frozen,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
