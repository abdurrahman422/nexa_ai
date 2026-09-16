"""One-time, content-bound approval controller for Gmail sends."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
from secrets import token_urlsafe
from threading import Lock
from typing import Any, Iterable

from app.schemas.gmail import GmailPreview, PreparedEmail


@dataclass(frozen=True)
class PendingEmailAction:
    approval_id: str
    content_hash: str
    preview: GmailPreview
    email: PreparedEmail
    expires_at: str


class EmailApprovalController:
    """Stores pending send requests separately from the GmailAgent.

    The agent can create a pending request, but has no agent method that marks
    it approved. Approval is a separate host/controller operation.
    """

    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl_seconds = ttl_seconds
        self._pending: dict[str, PendingEmailAction] = {}
        self._lock = Lock()

    @staticmethod
    def content_hash(email: PreparedEmail) -> str:
        canonical = "\n".join(
            [
                ",".join(email.to),
                ",".join(email.cc),
                ",".join(email.bcc),
                email.subject,
                email.body,
                email.thread_id or "",
                email.in_reply_to or "",
                " ".join(email.references),
                "|".join(f"{item.filename}:{item.size}:{item.attachment_id}" for item in email.attachments),
            ]
        )
        return sha256(canonical.encode("utf-8")).hexdigest()

    def create_pending(self, email: PreparedEmail, preview: GmailPreview) -> PendingEmailAction:
        now = datetime.now(timezone.utc)
        pending = PendingEmailAction(
            approval_id=token_urlsafe(24),
            content_hash=self.content_hash(email),
            preview=preview,
            email=email,
            expires_at=(now + timedelta(seconds=self.ttl_seconds)).isoformat(),
        )
        with self._lock:
            self._pending[pending.approval_id] = pending
        return pending

    def get_pending(self, approval_id: str) -> PendingEmailAction | None:
        with self._lock:
            pending = self._pending.get(approval_id)
            if pending is None:
                return None
            if datetime.now(timezone.utc) >= datetime.fromisoformat(pending.expires_at):
                self._pending.pop(approval_id, None)
                return None
            return pending

    def approve(self, approval_id: str, *, approved_by_user: bool) -> PendingEmailAction:
        if not approved_by_user:
            raise PermissionError("Explicit user approval is required.")
        pending = self.get_pending(approval_id)
        if pending is None:
            raise PermissionError("Approval is missing, expired, or already used.")
        with self._lock:
            self._pending.pop(approval_id, None)
        return pending


@dataclass(frozen=True)
class GmailApproval:
    approval_id: str
    draft_id: str
    active_account_id: str
    to: tuple[str, ...]
    cc: tuple[str, ...]
    bcc: tuple[str, ...]
    subject: str
    draft_fingerprint: str
    attachment_metadata: tuple[dict[str, Any], ...]
    created_at: str
    expires_at: str
    status: str


class GmailApprovalController:
    """Ephemeral, draft-only approval state with content binding."""

    def __init__(self, ttl_seconds: int = 300) -> None:
        if ttl_seconds <= 0:
            raise ValueError("Approval TTL must be positive and finite.")
        self.ttl_seconds = ttl_seconds
        self._approvals: dict[str, GmailApproval] = {}
        self._lock = Lock()

    @staticmethod
    def fingerprint(
        *,
        active_account_id: str,
        draft_id: str,
        email: PreparedEmail,
        attachment_metadata: tuple[dict[str, Any], ...],
    ) -> str:
        normalize_text = lambda value: str(value or "").replace("\r\n", "\n").replace("\r", "\n")
        normalize_recipients = lambda values: sorted(str(value).strip().casefold() for value in values)
        normalized_attachments = sorted(
            (dict(item) for item in attachment_metadata),
            key=lambda item: (
                str(item.get("filename", "")).casefold(),
                str(item.get("mime_type", "")).casefold(),
                int(item.get("size", 0)),
                str(item.get("content_sha256", "")),
            ),
        )
        canonical = {
            "active_account_id": active_account_id,
            "draft_id": draft_id,
            "to": normalize_recipients(email.to),
            "cc": normalize_recipients(email.cc),
            "bcc": normalize_recipients(email.bcc),
            "subject": normalize_text(email.subject),
            "body": normalize_text(email.body),
            "thread_id": email.thread_id,
            "in_reply_to": email.in_reply_to,
            "references": list(email.references),
            "attachments": normalized_attachments,
        }
        encoded = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return sha256(encoded).hexdigest()

    @staticmethod
    def _attachment_metadata(attachments: Iterable[Any]) -> tuple[dict[str, Any], ...]:
        metadata: list[dict[str, Any]] = []
        for attachment in attachments:
            content_hash: str | None = None
            local_path = getattr(attachment, "local_path", "")
            if local_path:
                digest = sha256()
                try:
                    with Path(local_path).open("rb") as file_handle:
                        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
                            digest.update(chunk)
                except OSError:
                    content_hash = None
                else:
                    content_hash = digest.hexdigest()
            metadata.append(
                {
                    "filename": str(getattr(attachment, "filename", "")),
                    "mime_type": str(getattr(attachment, "mime_type", "")),
                    "size": int(getattr(attachment, "size", 0)),
                    "attachment_id": str(getattr(attachment, "attachment_id", "")),
                    "content_sha256": content_hash,
                }
            )
        return tuple(metadata)

    def create_approval(
        self,
        draft_id: str,
        active_account_id: str,
        email: PreparedEmail,
        attachment_metadata: tuple[dict[str, Any], ...] | None = None,
    ) -> GmailApproval:
        if not draft_id or not active_account_id:
            raise ValueError("Draft and active Gmail account identifiers are required.")
        now = datetime.now(timezone.utc)
        attachment_metadata = attachment_metadata or self._attachment_metadata(email.attachments)
        approval = GmailApproval(
            approval_id=token_urlsafe(32),
            draft_id=draft_id,
            active_account_id=active_account_id,
            to=tuple(email.to),
            cc=tuple(email.cc),
            bcc=tuple(email.bcc),
            subject=email.subject,
            draft_fingerprint=self.fingerprint(
                active_account_id=active_account_id,
                draft_id=draft_id,
                email=email,
                attachment_metadata=attachment_metadata,
            ),
            attachment_metadata=attachment_metadata,
            created_at=now.isoformat(),
            expires_at=(now + timedelta(seconds=self.ttl_seconds)).isoformat(),
            status="pending",
        )
        with self._lock:
            self._approvals[approval.approval_id] = approval
        return approval

    def get_approval(self, approval_id: str) -> GmailApproval | None:
        self.expire_if_needed(approval_id)
        with self._lock:
            return self._approvals.get(approval_id)

    def expire_if_needed(self, approval_id: str) -> GmailApproval | None:
        with self._lock:
            approval = self._approvals.get(approval_id)
            if approval is None or approval.status not in {"pending", "approved"}:
                return approval
            if datetime.now(timezone.utc) < datetime.fromisoformat(approval.expires_at):
                return approval
            expired = GmailApproval(**{**approval.__dict__, "status": "expired"})
            self._approvals[approval_id] = expired
            return expired

    def is_valid(self, approval_id: str) -> bool:
        approval = self.get_approval(approval_id)
        return approval is not None and approval.status == "pending"

    def revalidate_approval(
        self,
        approval_id: str,
        *,
        active_account_id: str,
        draft_id: str,
        email: PreparedEmail | None,
        attachment_metadata: tuple[dict[str, Any], ...] = (),
    ) -> GmailApproval:
        approval = self.get_approval(approval_id)
        if approval is None:
            raise PermissionError("Approval was not found.")
        if approval.status in {"cancelled", "expired", "invalidated"}:
            return approval
        if (
            email is None
            or active_account_id != approval.active_account_id
            or draft_id != approval.draft_id
        ):
            return self.invalidate(approval_id)
        current_fingerprint = self.fingerprint(
            active_account_id=active_account_id,
            draft_id=draft_id,
            email=email,
            attachment_metadata=attachment_metadata or self._attachment_metadata(email.attachments),
        )
        if current_fingerprint != approval.draft_fingerprint:
            return self.invalidate(approval_id)
        return approval

    def approve(self, approval_id: str) -> GmailApproval:
        with self._lock:
            approval = self._approvals.get(approval_id)
            if approval is None:
                raise PermissionError("Approval was not found.")
            if approval.status != "pending":
                raise PermissionError(f"Approval cannot be approved from status '{approval.status}'.")
            if datetime.now(timezone.utc) >= datetime.fromisoformat(approval.expires_at):
                expired = GmailApproval(**{**approval.__dict__, "status": "expired"})
                self._approvals[approval_id] = expired
                raise PermissionError("Approval has expired.")
            approved = GmailApproval(**{**approval.__dict__, "status": "approved"})
            self._approvals[approval_id] = approved
            return approved

    def cancel(self, approval_id: str) -> GmailApproval:
        approval = self.expire_if_needed(approval_id)
        if approval is not None and approval.status == "expired":
            raise PermissionError("Approval has expired.")
        return self._transition_pending(approval_id, "cancelled")

    def invalidate(self, approval_id: str) -> GmailApproval:
        approval = self.expire_if_needed(approval_id)
        if approval is not None and approval.status == "expired":
            return approval
        with self._lock:
            approval = self._approvals.get(approval_id)
            if approval is None:
                raise PermissionError("Approval was not found.")
            if approval.status in {"cancelled", "expired", "invalidated"}:
                return approval
            invalidated = GmailApproval(**{**approval.__dict__, "status": "invalidated"})
            self._approvals[approval_id] = invalidated
            return invalidated

    def _transition_pending(self, approval_id: str, status: str) -> GmailApproval:
        with self._lock:
            approval = self._approvals.get(approval_id)
            if approval is None:
                raise PermissionError("Approval was not found.")
            if approval.status != "pending":
                raise PermissionError(f"Approval cannot be {status} from status '{approval.status}'.")
            transitioned = GmailApproval(**{**approval.__dict__, "status": status})
            self._approvals[approval_id] = transitioned
            return transitioned
