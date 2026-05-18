from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.commands import router as commands_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(commands_router, prefix="/api")


@app.get("/")
def root() -> dict[str, str]:
    return {
        "app": settings.app_name,
        "status": "running",
        "version": settings.app_version,
        "environment": settings.app_env,
    }
