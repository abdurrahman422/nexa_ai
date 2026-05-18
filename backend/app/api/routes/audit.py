"""Audit preview API routes for the Nexa AI backend."""

from fastapi import APIRouter, Depends

from app.audit import AuditRepository
from app.audit import SQLiteAuditRepository
from app.audit import get_audit_migration_preview
from app.schemas import AuditLogRequest
from app.schemas import AuditLogResponse
from app.schemas import AuditRouteHealth
from app.schemas import AuditMigrationPreviewResponse
from app.schemas import create_audit_response

router = APIRouter(prefix="/audit", tags=["audit"])


def get_audit_repository() -> AuditRepository:
    """Provide an AuditRepository instance per request."""
    return AuditRepository()


def get_sqlite_repository() -> SQLiteAuditRepository:
    """Provide a SQLiteAuditRepository instance per request."""
    return SQLiteAuditRepository()


@router.get("/health", response_model=AuditRouteHealth)
def audit_route_health(
    repo: AuditRepository = Depends(get_audit_repository),
    sqlite_repo: SQLiteAuditRepository = Depends(get_sqlite_repository),
) -> AuditRouteHealth:
    """Return health status for the audit preview module."""
    status = repo.preview_storage_status()
    sqlite_status = sqlite_repo.get_storage_status()
    return AuditRouteHealth(
        status="ok",
        module="audit_preview",
        phase="20.4",
        storage_enabled=False,
        execution_enabled=False,
        storage_mode=status["storage_mode"],
        message=status["message"],
        sqlite_available=sqlite_status["available"],
        sqlite_writes_enabled=False,
        sqlite_database_path=sqlite_status["database_path"],
        sqlite_table_name=sqlite_status["table_name"],
    )


@router.post("/preview", response_model=AuditLogResponse)
def preview_audit_log(
    request: AuditLogRequest,
    repo: AuditRepository = Depends(get_audit_repository),
    sqlite_repo: SQLiteAuditRepository = Depends(get_sqlite_repository),
) -> AuditLogResponse:
    """Return a preview-only audit response.

    No database storage or real execution occurs.
    stored is always False, execution_enabled is always False.
    """
    repo.save_preview(request)
    sqlite_result = sqlite_repo.insert_audit_log(request)
    response = create_audit_response(request)
    response.storage_backend = sqlite_result["storage_backend"]
    response.storage_message = sqlite_result["reason"]
    return response


@router.get("/migration/preview", response_model=AuditMigrationPreviewResponse)
def audit_migration_preview() -> AuditMigrationPreviewResponse:
    """Return a read-only preview of the SQLite audit migration script.

    No database connection, no SQL execution, no table creation.
    """
    preview = get_audit_migration_preview()
    return AuditMigrationPreviewResponse(
        status="preview_only",
        script_path=preview.script_path,
        exists=preview.exists,
        can_run=False,
        migrations_enabled=False,
        statement_count=preview.statement_count,
        table_name=preview.table_name,
        preview_message=preview.preview_message,
        safety_notes=preview.safety_notes,
        execution_enabled=False,
    )
