"""Controlled Gmail API routes backed by NEXA's GmailAgent."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, EmailStr, Field

from app.agents.gmail_agent import format_agent_result, get_gmail_agent
from app.audit.event_log import record_audit_event
from app.permissions import is_permission_enabled, permission_denied_message

router = APIRouter(prefix="/gmail", tags=["gmail"])


class GmailRequest(BaseModel):
    action: str = "search"
    query: str = ""
    message_id: str | None = None
    thread_id: str | None = None
    sender: EmailStr | None = None
    subject: str | None = None
    after: str | None = None
    before: str | None = None
    label_ids: list[str] = Field(default_factory=list)
    attachment_id: str | None = None
    output_dir: str = "attachments"
    to: list[EmailStr] = Field(default_factory=list)
    cc: list[EmailStr] = Field(default_factory=list)
    bcc: list[EmailStr] = Field(default_factory=list)
    body: str = ""
    attachments: list[dict[str, str]] = Field(default_factory=list)
    user_email: EmailStr | None = None
    limit: int = Field(default=20, ge=1, le=100)


class GmailApprovalRequest(BaseModel):
    approved: bool = False


def _blocked(action: str, permission: str) -> dict:
    message = permission_denied_message(permission)
    record_audit_event("gmail", action, "blocked", "permission", "", message)
    return {
        "status": "blocked",
        "action": action,
        "executed": False,
        "message": message,
        "error": "permission_disabled",
    }


@router.get("/capabilities")
def gmail_capabilities() -> dict:
    enabled = is_permission_enabled("gmail_skill")
    return {
        "available": True,
        "enabled": enabled,
        "provider": "MockGmailProvider",
        "actions": [
            "search", "read", "thread", "unread", "sender", "subject", "date",
            "attachments", "download_attachment", "labels", "add_labels",
            "remove_labels", "archive", "draft", "reply_draft", "reply_all_draft",
            "prepare_send",
        ],
        "direct_send": False,
        "message": "Gmail is controlled by GmailAgent; sending requires a separate user approval.",
    }


@router.post("/command")
def gmail_command(request: GmailRequest) -> dict:
    if not is_permission_enabled("gmail_skill"):
        return _blocked(request.action, "gmail_skill")
    kwargs = request.model_dump(exclude_none=True)
    kwargs.pop("action", None)
    result = get_gmail_agent().execute(request.action, **kwargs)
    return format_agent_result(result)


@router.post("/approvals/{approval_id}/approve")
def approve_gmail_send(approval_id: str, request: GmailApprovalRequest) -> dict:
    if not request.approved:
        return {
            "status": "blocked",
            "action": "send",
            "executed": False,
            "message": "Explicit user approval is required; no email was sent.",
            "error": "approval_required",
        }
    result = get_gmail_agent().approve_and_send(approval_id)
    return format_agent_result(result)