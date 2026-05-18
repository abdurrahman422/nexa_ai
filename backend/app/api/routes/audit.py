"""Audit preview API routes for the Nexa AI backend."""

from fastapi import APIRouter

from app.schemas import AuditLogRequest
from app.schemas import AuditLogResponse
from app.schemas import AuditRouteHealth
from app.schemas import create_audit_response

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/health", response_model=AuditRouteHealth)
def audit_route_health() -> AuditRouteHealth:
    """Return health status for the audit preview module."""
    return AuditRouteHealth(
        status="ok",
        module="audit_preview",
        phase="18.2",
        storage_enabled=False,
        execution_enabled=False,
    )


@router.post("/preview", response_model=AuditLogResponse)
def preview_audit_log(
    request: AuditLogRequest,
) -> AuditLogResponse:
    """Return a preview-only audit response.

    No database storage or real execution occurs.
    stored is always False, execution_enabled is always False.
    """
    return create_audit_response(request)
