"""Typed Gmail data contracts used by the NEXA agent and providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GmailAttachment:
    filename: str
    mime_type: str
    size: int
    attachment_id: str


@dataclass(frozen=True)
class GmailEmail:
    id: str
    thread_id: str
    sender: str
    recipients: tuple[str, ...]
    cc: tuple[str, ...]
    subject: str
    date: str
    snippet: str
    body_text: str
    labels: tuple[str, ...] = ()
    attachments: tuple[GmailAttachment, ...] = ()
    reply_to: str | None = None
    message_id: str | None = None
    references: tuple[str, ...] = ()


@dataclass(frozen=True)
class GmailThread:
    id: str
    messages: tuple[GmailEmail, ...]


@dataclass(frozen=True)
class PreparedEmail:
    to: tuple[str, ...]
    cc: tuple[str, ...]
    bcc: tuple[str, ...]
    subject: str
    body: str
    attachments: tuple[GmailAttachment, ...] = ()
    thread_id: str | None = None
    in_reply_to: str | None = None
    references: tuple[str, ...] = ()


@dataclass(frozen=True)
class GmailPreview:
    sender: str
    recipients: tuple[str, ...]
    subject: str
    date: str
    snippet: str
    labels: tuple[str, ...]
    attachments: tuple[GmailAttachment, ...]
    untrusted_content: bool = True
    security_flags: tuple[str, ...] = ()


@dataclass(frozen=True)
class GmailActionResult:
    status: str
    action: str
    message: str
    emails: tuple[GmailEmail, ...] = ()
    thread: GmailThread | None = None
    preview: GmailPreview | None = None
    draft_id: str | None = None
    approval_id: str | None = None
    attachment_path: str | None = None
    labels: tuple[dict[str, str], ...] = ()
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
