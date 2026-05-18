"""Audit repository placeholder for the Nexa AI backend.

No database storage is enabled in this phase.
All save operations return a disabled-storage response.
"""

from app.audit.storage_config import get_audit_storage_config
from app.schemas import AuditLogRequest


class AuditRepository:
    """Repository for audit log operations.

    Storage is disabled by default. No real persistence occurs.
    """

    def __init__(self) -> None:
        self._config = get_audit_storage_config()

    def is_storage_enabled(self) -> bool:
        """Return whether audit storage is currently enabled."""
        return self._config.storage_enabled

    def preview_storage_status(self) -> dict:
        """Return the current storage status overview."""
        return {
            "storage_enabled": False,
            "storage_mode": "disabled",
            "message": "Audit storage is prepared but disabled in this phase.",
        }

    def save_preview(self, request: AuditLogRequest) -> dict:
        """Attempt to save an audit record.

        Storage is disabled — this method does NOT write to any database or file.
        """
        return {
            "stored": False,
            "storage_enabled": False,
            "message": "Audit storage is disabled. Record was not persisted.",
        }
