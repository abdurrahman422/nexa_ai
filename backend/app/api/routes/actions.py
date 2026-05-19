"""API routes for safe action execution."""

from fastapi import APIRouter

from app.schemas import ActionExecutionRequest
from app.schemas import ActionExecutionResponse
from app.schemas import FileSearchRequest
from app.schemas import FileSearchResponse
from app.actions import execute_open_website
from app.actions import execute_open_app
from app.files import search_files_read_only

router = APIRouter(prefix="/actions", tags=["actions"])


@router.get("/health")
def actions_health() -> dict:
    return {
        "status": "ok",
        "module": "safe_actions",
        "phase": "32.3",
        "website_execution_available": True,
        "app_execution_available": True,
        "file_search_available": True,
        "requires_confirmation": True,
    }


@router.post("/website/open")
def open_website_action(request: ActionExecutionRequest) -> ActionExecutionResponse:
    return execute_open_website(request)


@router.post("/app/open")
def open_app_action(request: ActionExecutionRequest) -> ActionExecutionResponse:
    return execute_open_app(request)


@router.post("/files/search")
def file_search_action(request: FileSearchRequest) -> FileSearchResponse:
    return search_files_read_only(request)
