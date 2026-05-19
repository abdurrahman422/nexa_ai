import uvicorn

from app.core.config import get_settings


def main() -> None:
    settings = get_settings()

    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=int(settings.backend_port),
        reload=settings.app_env == "development",
    )


if __name__ == "__main__":
    main()
