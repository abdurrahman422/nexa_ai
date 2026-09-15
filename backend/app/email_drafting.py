"""English-only email composition before Gmail draft creation."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any

from app.llm import complete as complete_llm

STYLE_MARKERS = (
    "formal",
    "professional",
    "polite",
    "friendly",
    "concise",
    "short",
    "academic",
    "business",
    "apology",
    "reminder",
    "follow-up",
    "request",
)


@dataclass(frozen=True)
class EmailDraftComposition:
    to: tuple[str, ...]
    cc: tuple[str, ...]
    bcc: tuple[str, ...]
    subject: str
    body: str
    tone: str
    styles: tuple[str, ...]

    def as_kwargs(self) -> dict[str, Any]:
        return {
            "to": self.to,
            "cc": self.cc,
            "bcc": self.bcc,
            "subject": self.subject,
            "body": self.body,
            "draft_tone": self.tone,
            "draft_styles": self.styles,
        }


def compose_missing_fields(
    request: str,
    *,
    to: tuple[str, ...],
    cc: tuple[str, ...] = (),
    bcc: tuple[str, ...] = (),
    subject: str = "",
    body: str = "",
) -> EmailDraftComposition:
    styles = tuple(marker for marker in STYLE_MARKERS if re.search(rf"\b{re.escape(marker)}\b", request, re.IGNORECASE))
    tone = _tone_for(styles)
    purpose = _purpose(request, to)
    generated_subject, generated_body = _generate(request, purpose, tone, styles)
    return EmailDraftComposition(
        to=to,
        cc=cc,
        bcc=bcc,
        subject=subject.strip() or generated_subject,
        body=body.strip() or generated_body,
        tone=tone,
        styles=styles,
    )


def _purpose(request: str, recipients: tuple[str, ...]) -> str:
    without_recipients = request
    for recipient in recipients:
        without_recipients = without_recipients.replace(recipient, "", 1)
    match = re.search(
        r"\b(?:about|regarding|because|confirming|to discuss|on)\s+(.+?)(?=\s+(?:subject|body|cc|bcc|to)\s*:|$)",
        without_recipients,
        re.IGNORECASE | re.DOTALL,
    )
    if match:
        return match.group(1).strip().strip(".")
    lowered = request.lower()
    if "payment" in lowered:
        return "the payment"
    if "project delay" in lowered:
        return "the project delay"
    if "missed" in lowered or "apolog" in lowered:
        return "the missed commitment"
    if "meeting" in lowered:
        return "the meeting"
    return "the matter described in your request"


def _tone_for(styles: tuple[str, ...]) -> str:
    for marker in ("formal", "professional", "polite", "friendly", "academic", "business", "apology", "reminder"):
        if marker in styles:
            return marker
    return "professional"


def _generate(request: str, purpose: str, tone: str, styles: tuple[str, ...]) -> tuple[str, str]:
    generated = _llm_generation(request, purpose, tone, styles)
    if generated is not None:
        return generated
    subject = _fallback_subject(purpose, styles)
    body = _fallback_body(purpose, tone, styles)
    return subject, body


def _llm_generation(request: str, purpose: str, tone: str, styles: tuple[str, ...]) -> tuple[str, str] | None:
    prompt = (
        "Draft an English email from the user's request. Return JSON only with string keys "
        "subject and body. Keep it concise and professional. Do not invent dates, names, "
        "reasons, deadlines, or promises; use neutral wording or [Your Name] when needed. "
        f"Requested style: {', '.join(styles) or tone}. Purpose: {purpose}. User request: {request}"
    )
    try:
        result = complete_llm(prompt, language_style="english", context="Email drafting only; do not send or mutate Gmail.")
        if result is None:
            return None
        data = json.loads(result.answer)
        if not isinstance(data, dict) or not isinstance(data.get("subject"), str) or not isinstance(data.get("body"), str):
            return None
        if data["subject"].strip() and data["body"].strip():
            return data["subject"].strip(), data["body"].strip()
    except (Exception, json.JSONDecodeError):
        return None
    return None


def _fallback_subject(purpose: str, styles: tuple[str, ...]) -> str:
    lowered = purpose.lower()
    if "late" in lowered and ("submission" in lowered or "project" in lowered):
        return "Apology for Late Project Submission"
    if "class" in lowered and ("missed" in lowered or "absent" in lowered):
        return "Apology for Missing Class"
    if "meeting" in lowered or "confirm" in lowered:
        return "Meeting Confirmation"
    if "payment" in lowered or "remind" in lowered:
        return "Payment Reminder"
    if "follow-up" in lowered or "follow up" in lowered or "follow-up" in styles:
        return "Follow-up"
    if "apolog" in lowered or "missed" in lowered:
        return "Apology"
    if "delay" in lowered:
        return "Project Delay"
    words = purpose.split()
    return "Regarding " + " ".join(words[:8]).rstrip(".") if words else "Email Request"


def _fallback_body(purpose: str, tone: str, styles: tuple[str, ...]) -> str:
    lowered = purpose.lower()
    greeting = "Dear Professor," if "academic" in styles or "professor" in lowered else "Hello,"
    if "late" in lowered and ("submission" in lowered or "project" in lowered):
        return (
            f"{greeting}\n\n"
            "I sincerely apologize for the delay in submitting my project. "
            "I understand the importance of meeting the submission deadline and regret any inconvenience this may have caused.\n\n"
            "I would be grateful if you would kindly accept my late submission. "
            "Please let me know if any additional steps or information are required.\n\n"
            "Thank you for your understanding.\n\n"
            "Best regards,\n[Your Name]"
        )
    if "class" in lowered and ("missed" in lowered or "absent" in lowered):
        return (
            f"{greeting}\n\n"
            f"I apologize for missing {purpose.split('missed', 1)[-1].strip() if 'missed' in lowered else 'class'}.\n\n"
            "Could you please let me know what material was covered and whether there are any steps I should take to catch up?\n\n"
            "Thank you for your guidance.\n\n"
            "Best regards,\n[Your Name]"
        )
    if "payment" in lowered or "remind" in lowered:
        return (
            f"{greeting}\n\n"
            f"I am writing to kindly remind you about {purpose}.\n\n"
            "Could you please arrange the payment at your earliest convenience?\n\n"
            "Thank you for your attention to this matter.\n\n"
            "Best regards,\n[Your Name]"
        )
    if "meeting" in lowered or "confirm" in lowered:
        return (
            f"{greeting}\n\n"
            f"I am writing to confirm {purpose}.\n\n"
            "Please let me know if this arrangement is convenient.\n\n"
            "Best regards,\n[Your Name]"
        )
    if "follow-up" in lowered or "follow up" in lowered or "follow-up" in styles:
        return (
            f"{greeting}\n\n"
            f"I am following up regarding {purpose}.\n\n"
            "I would appreciate any update when convenient.\n\n"
            "Thank you for your time.\n\n"
            "Best regards,\n[Your Name]"
        )
    if "delay" in lowered:
        return (
            f"{greeting}\n\n"
            f"I am writing to provide an update regarding {purpose}.\n\n"
            "The project is delayed, and I wanted to keep you informed. I will share further information when available.\n\n"
            "Thank you for your understanding.\n\n"
            "Best regards,\n[Your Name]"
        )
    if "apolog" in lowered or "missed" in lowered:
        return (
            f"{greeting}\n\nI sincerely apologize regarding {purpose}.\n\n"
            "Please let me know how I can address this appropriately.\n\n"
            "Thank you for your understanding.\n\nBest regards,\n[Your Name]"
        )
    if "request" in lowered:
        return (
            f"{greeting}\n\nI am writing to request your assistance regarding {purpose}.\n\n"
            "I would appreciate your guidance on this matter.\n\nBest regards,\n[Your Name]"
        )
    return f"{greeting}\n\nI am writing regarding {purpose}.\n\nThank you for your time and consideration.\n\nBest regards,\n[Your Name]"
