"""API routes for safe action execution."""

from fastapi import APIRouter

from app.schemas import ActionExecutionRequest
from app.schemas import ActionExecutionResponse
from app.actions import execute_open_website
from app.actions import execute_open_app

router = APIRouter(prefix="/actions", tags=["actions"])


@router.get("/health")
def actions_health() -> dict:
    return {
        "status": "ok",
        "module": "safe_actions",
        "phase": "29.3",
        "website_execution_available": True,
        "app_execution_available": True,
        "file_search_available": False,
        "requires_confirmation": True,
    }


@router.post("/website/open")
def open_website_action(request: ActionExecutionRequest) -> ActionExecutionResponse:
    return execute_open_website(request)


@router.post("/app/open")
def open_app_action(request: ActionExecutionRequest) -> ActionExecutionResponse:
    return execute_open_app(request)
