"""Controlled Gmail API routes backed by NEXA's GmailAgent."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, EmailStr, Field

from app.agents.gmail_agent import format_agent_result, get_gmail_agent
from app.audit.event_log import record_audit_event
from app.permissions import is_permission_enabled, permission_denied_message
from app.schemas.gmail import GmailAttachment, PreparedEmail

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
    open_browser: bool = True
    limit: int = Field(default=20, ge=1, le=100)


class GmailApprovalRequest(BaseModel):
    approved: bool = False


class GmailDraftApprovalRequest(BaseModel):
    draft_id: str = Field(min_length=1)
    to: list[EmailStr] = Field(default_factory=list)
    cc: list[EmailStr] = Field(default_factory=list)
    bcc: list[EmailStr] = Field(default_factory=list)
    subject: str = ""
    body: str = ""
    attachments: list[dict[str, object]] = Field(default_factory=list)


class GmailAccountRequest(BaseModel):
    account_id: str


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
    provider = get_gmail_agent().provider.__class__.__name__
    return {
        "available": True,
        "enabled": enabled,
        "provider": provider,
        "actions": [
            "search", "read", "thread", "unread", "sender", "subject", "date",
            "attachments", "download_attachment", "labels", "add_labels",
            "remove_labels", "archive", "draft", "reply_draft", "reply_all_draft", "forward_draft",
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


def _draft_approval_response(approval: object | None) -> dict:
    if approval is None:
        return {"status": "not_found", "approval": None}
    data = {
        key: getattr(approval, key)
        for key in (
            "approval_id", "draft_id", "active_account_id", "to", "cc", "bcc",
            "subject", "draft_fingerprint", "attachment_metadata", "created_at",
            "expires_at", "status",
        )
    }
    data["to"] = list(data["to"])
    data["cc"] = list(data["cc"])
    data["bcc"] = list(data["bcc"])
    data["attachment_metadata"] = list(data["attachment_metadata"])
    return {"status": data["status"], "approval": data}


def _prepared_email(request: GmailDraftApprovalRequest) -> PreparedEmail:
    attachments = tuple(
        GmailAttachment(
            filename=str(item.get("filename", "")),
            mime_type=str(item.get("mime_type", "application/octet-stream")),
            size=int(item.get("size", 0)),
            attachment_id=str(item.get("attachment_id", "")),
            local_path=str(item.get("local_path", "")),
        )
        for item in request.attachments
    )
    return PreparedEmail(
        to=tuple(str(item) for item in request.to),
        cc=tuple(str(item) for item in request.cc),
        bcc=tuple(str(item) for item in request.bcc),
        subject=request.subject,
        body=request.body,
        attachments=attachments,
    )


@router.post("/draft-approvals")
def request_gmail_draft_approval(request: GmailDraftApprovalRequest) -> dict:
    if not is_permission_enabled("gmail_skill"):
        return _blocked("draft_approval", "gmail_skill")
    approval = get_gmail_agent().request_draft_approval(request.draft_id, _prepared_email(request))
    return _draft_approval_response(approval)


@router.get("/draft-approvals/{approval_id}")
def get_gmail_draft_approval(approval_id: str) -> dict:
    return _draft_approval_response(get_gmail_agent().get_draft_approval(approval_id))


@router.post("/draft-approvals/{approval_id}/approve")
def approve_gmail_draft(approval_id: str) -> dict:
    try:
        return _draft_approval_response(get_gmail_agent().approve_draft(approval_id))
    except PermissionError as exc:
        return {"status": "blocked", "approval": None, "error": str(exc)}


@router.post("/draft-approvals/{approval_id}/cancel")
def cancel_gmail_draft_approval(approval_id: str) -> dict:
    try:
        return _draft_approval_response(get_gmail_agent().cancel_draft(approval_id))
    except PermissionError as exc:
        return {"status": "blocked", "approval": None, "error": str(exc)}


@router.get("/accounts")
def gmail_accounts() -> dict:
    provider = get_gmail_agent().provider
    accounts = provider.list_accounts() if hasattr(provider, "list_accounts") else []
    active = provider.active_account() if hasattr(provider, "active_account") else None
    return {"accounts": accounts, "active_account": active}


@router.get("/accounts/active")
def gmail_active_account() -> dict:
    provider = get_gmail_agent().provider
    active = provider.active_account() if hasattr(provider, "active_account") else None
    return {"account": active}


@router.get("/accounts/connect-status")
def gmail_connect_status() -> dict:
    provider = get_gmail_agent().provider
    status = getattr(provider, "authorization_status", None)
    return status() if status is not None else {"provider": provider.__class__.__name__, "state": "idle", "error": None}


@router.post("/accounts/connect")
def gmail_connect_account(request: GmailRequest | None = None) -> dict:
    provider = get_gmail_agent().provider
    begin_authorization = getattr(provider, "begin_authorization", None)
    if begin_authorization is not None:
        return {"status": "pending", "action": "authorize", "message": "Gmail authorization started in the default browser." , "metadata": begin_authorization()}
    result = get_gmail_agent().execute("authorize", open_browser=request.open_browser if request else True)
    return format_agent_result(result)


@router.post("/accounts/switch")
def gmail_switch_account(request: GmailAccountRequest) -> dict:
    provider = get_gmail_agent().provider
    try:
        account = provider.switch_account(request.account_id)
        return {"status": "completed", "account": account}
    except AttributeError:
        return {"status": "failed", "message": "Gmail account switching is available only for the Google provider.", "error": "unsupported_provider"}
    except Exception as exc:
        return {"status": "failed", "message": str(exc), "error": str(exc)}


@router.post("/accounts/disconnect")
def gmail_disconnect_account(request: GmailAccountRequest) -> dict:
    provider = get_gmail_agent().provider
    try:
        provider.disconnect_account(request.account_id)
        return {"status": "completed", "account_id": request.account_id}
    except AttributeError:
        return {"status": "failed", "message": "Gmail account disconnect is available only for the Google provider.", "error": "unsupported_provider"}
    except Exception as exc:
        return {"status": "failed", "message": str(exc), "error": str(exc)}