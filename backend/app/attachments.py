"""Safe local attachment resolution and validation for Gmail drafts."""

from __future__ import annotations

import mimetypes
from pathlib import Path
import os

from app.providers.gmail_provider import GmailProviderError
from app.schemas.gmail import GmailAttachment

MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
MAX_TOTAL_ATTACHMENT_BYTES = 25 * 1024 * 1024
_SENSITIVE_NAMES = {"token.json", "credentials.json", ".env"}
_SENSITIVE_SUFFIXES = {".pem", ".key", ".p12"}


def resolve_attachments(values: object) -> tuple[GmailAttachment, ...]:
    if values is None:
        return ()
    if isinstance(values, (str, Path)):
        values = (values,)
    if not isinstance(values, (list, tuple)):
        raise GmailProviderError("Attachment paths must be a list.")
    attachments: list[GmailAttachment] = []
    for value in values:
        path_value = value.get("path") if isinstance(value, dict) else value
        if not isinstance(path_value, (str, Path)) or not str(path_value).strip():
            raise GmailProviderError("Each attachment must provide a valid local file path.")
        path = Path(str(path_value).strip().strip('"')).expanduser()
        if not path.is_absolute():
            matches = _safe_filename_matches(path.name)
            if len(matches) != 1:
                raise GmailProviderError(f"Please provide the exact file path for {path.name}.")
            path = matches[0]
        path = path.resolve()
        _validate_path(path)
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        attachments.append(GmailAttachment(path.name, mime_type, path.stat().st_size, "", str(path), "validated"))
    total = sum(item.size for item in attachments)
    if total > MAX_TOTAL_ATTACHMENT_BYTES:
        raise GmailProviderError("Attachments exceed the total Gmail message size limit.")
    return tuple(attachments)


def _validate_path(path: Path) -> None:
    lowered = path.name.casefold()
    if lowered in _SENSITIVE_NAMES or path.suffix.casefold() in _SENSITIVE_SUFFIXES:
        raise GmailProviderError(f"Attachment blocked for safety: {path.name}.")
    normalized = str(path).replace("\\", "/").casefold()
    if "/nexa-secrets/" in normalized or "/.nexa_ai/gmail/" in normalized:
        raise GmailProviderError(f"Attachment blocked for safety: {path.name}.")
    if not path.exists():
        raise GmailProviderError(f"Attachment file was not found: {path.name}.")
    if not path.is_file():
        raise GmailProviderError(f"Attachment must be a regular file: {path.name}.")
    if not os.access(path, os.R_OK):
        raise GmailProviderError(f"Attachment is not readable: {path.name}.")
    if path.stat().st_size > MAX_ATTACHMENT_BYTES:
        raise GmailProviderError(f"Attachment is too large: {path.name}.")


def _safe_filename_matches(filename: str) -> list[Path]:
    roots = (Path.cwd(), Path.home() / "Documents", Path.home() / "Downloads")
    return [candidate for root in roots if root.is_dir() for candidate in root.glob(filename) if candidate.is_file()]


def sanitize_attachment(item: GmailAttachment) -> dict[str, object]:
    return {"file_name": item.filename, "mime_type": item.mime_type, "size_bytes": item.size, "exists": True, "safe_status": item.safe_status or "validated"}
