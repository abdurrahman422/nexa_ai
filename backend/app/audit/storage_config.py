"""Audit storage configuration for the Nexa AI backend."""

from dataclasses import dataclass


@dataclass
class AuditStorageConfig:
    """Configuration for audit log storage.

    Storage is disabled by default in the current phase.
    No database connection or file writes are made.
    """

    storage_enabled: bool = False
    storage_mode: str = "disabled"
    database_table: str = "audit_logs"
    max_preview_records: int = 0


def get_audit_storage_config() -> AuditStorageConfig:
    """Return the default audit storage configuration.

    Storage is disabled — no database writes, no file writes.
    """
    return AuditStorageConfig()
