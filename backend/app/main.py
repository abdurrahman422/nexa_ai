from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.commands import router as commands_router
from app.api.routes.audit import router as audit_router
from app.api.routes.database import router as database_router
from app.api.routes.health import router as health_router
from app.api.routes.actions import router as actions_router
from app.api.routes.voice import router as voice_router
from app.api.routes.permissions import router as permissions_router
from app.api.routes.web import router as web_router
from app.api.routes.documents import router as documents_router
from app.api.routes.reminders import router as reminders_router
from app.api.routes.chat import router as chat_router
from app.api.routes.contacts import router as contacts_router
from app.api.routes.youtube import router as youtube_router
from app.api.routes.images import router as images_router
from app.api.routes.system_controls import router as system_controls_router
from app.api.routes.content import router as content_router
from app.api.routes.setup import router as setup_router
from app.api.routes.productivity import router as productivity_router
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
        "null",  # Electron production renderer loaded from file://
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(commands_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(database_router, prefix="/api")
app.include_router(actions_router, prefix="/api")
app.include_router(voice_router, prefix="/api")
app.include_router(permissions_router, prefix="/api")
app.include_router(web_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(reminders_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(contacts_router, prefix="/api")
app.include_router(youtube_router, prefix="/api")
app.include_router(images_router, prefix="/api")
app.include_router(system_controls_router, prefix="/api")
app.include_router(content_router, prefix="/api")
app.include_router(setup_router, prefix="/api")
app.include_router(productivity_router, prefix="/api")


@app.get("/")
def root() -> dict[str, str]:
    return {
        "app": settings.app_name,
        "status": "running",
        "version": settings.app_version,
        "environment": settings.app_env,
    }
