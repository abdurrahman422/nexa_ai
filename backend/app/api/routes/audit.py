"""Audit preview API routes for the Nexa AI backend."""

from fastapi import APIRouter, Depends

from app.audit import AuditRepository
from app.schemas import AuditLogRequest
from app.schemas import AuditLogResponse
from app.schemas import AuditRouteHealth
from app.schemas import create_audit_response

router = APIRouter(prefix="/audit", tags=["audit"])


def get_audit_repository() -> AuditRepository:
    """Provide an AuditRepository instance per request."""
    return AuditRepository()


@router.get("/health", response_model=AuditRouteHealth)
def audit_route_health(
    repo: AuditRepository = Depends(get_audit_repository),
) -> AuditRouteHealth:
    """Return health status for the audit preview module."""
    status = repo.preview_storage_status()
    return AuditRouteHealth(
        status="ok",
        module="audit_preview",
        phase="19.3",
        storage_enabled=False,
        execution_enabled=False,
        storage_mode=status["storage_mode"],
        message=status["message"],
    )


@router.post("/preview", response_model=AuditLogResponse)
def preview_audit_log(
    request: AuditLogRequest,
    repo: AuditRepository = Depends(get_audit_repository),
) -> AuditLogResponse:
    """Return a preview-only audit response.

    No database storage or real execution occurs.
    stored is always False, execution_enabled is always False.
    """
    repo.save_preview(request)
    return create_audit_response(request)
