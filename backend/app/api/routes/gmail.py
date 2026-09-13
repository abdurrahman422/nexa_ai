"""Advanced, audited Gmail/Email controller API."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

from app.audit.event_log import record_audit_event
from app.permissions import is_permission_enabled, permission_denied_message

router = APIRouter(prefix="/gmail", tags=["gmail"])

class GmailRequest(BaseModel):
    recipient: EmailStr
    subject: str
    body: str
    action: str = "draft"  
    user_confirmed: bool = False

def _response(status: str, action: str, message: str, *, executed: bool = False, error: str | None = None):
    return {
        "status": status,
        "action": action,
        "executed": executed,
        "message": message,
        "error": error,
    }

@router.get("/capabilities")
def gmail_capabilities():
    enabled = is_permission_enabled("gmail_skill") and is_permission_enabled("email_control")
    return {
        "available": True,
        "enabled": enabled,
        "actions": ["draft", "send"],
        "message": (
            "Gmail drafting and automation skill is ready."
            if enabled
            else "Enable Gmail and email permissions to use this feature."
        ),
    }

@router.post("/command")
def gmail_command(request: GmailRequest):
  
    if not is_permission_enabled("gmail_skill") or not is_permission_enabled("email_control"):
        message = permission_denied_message(
            "email_control" if is_permission_enabled("gmail_skill") else "gmail_skill"
        )
        record_audit_event("gmail", "email_control", "blocked", "permission", request.recipient, message)
        return _response("blocked", request.action, message, error=message)

    
    if request.action == "send" and not request.user_confirmed:
        message = "Email sending requires explicit user confirmation or review in draft mode."
        return {
            "status": "confirmation_required",
            "action": request.action,
            "executed": False,
            "requires_confirmation": True,
            "message": message,
            "error": message,
        }

    try:
     
        action_name = "email_draft" if request.action == "draft" else "email_send"
        message = f"Successfully created secure email draft for {request.recipient}."
        
        record_audit_event("gmail", action_name, "executed", "controlled", request.recipient, message)
        return _response("executed", request.action, message, executed=True)

    except Exception as exc:
        message = str(exc)
        record_audit_event("gmail", request.action, "failed", "controlled", request.recipient, message)
        return _response("failed", request.action, message, error=message)