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
    open_browser: bool = True
    limit: int = Field(default=20, ge=1, le=100)


class GmailApprovalRequest(BaseModel):
    approved: bool = False


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