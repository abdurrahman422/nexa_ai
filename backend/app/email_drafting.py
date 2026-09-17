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
    profile_name: str = "",
) -> EmailDraftComposition:
    styles = tuple(marker for marker in STYLE_MARKERS if re.search(rf"\b{re.escape(marker)}\b", request, re.IGNORECASE))
    tone = _tone_for(styles)
    purpose = _purpose(request, to)
    generated_subject, generated_body = _generate(request, purpose, tone, styles, profile_name)
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
        r"\b(?:about|regarding|because|confirming|to discuss|on|for|requesting)\s+(.+?)(?=\s+(?:subject|body|cc|bcc|to)\s*:|$)",
        without_recipients,
        re.IGNORECASE | re.DOTALL,
    )
    if match:
        return match.group(1).strip().strip(".")
    lowered = request.lower()
    if "extension" in lowered:
        return "my request for a brief extension"
    if "timeline" in lowered or "milestone" in lowered or "risk" in lowered:
        return "the project update, current timeline, and next milestone"
    if "proposal" in lowered:
        return "the proposal"
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


def _clean_profile_name(name: str | None) -> str:
    cleaned = " ".join(str(name or "").replace("[Your Name]", "").split())
    return cleaned.strip()


def _closing_line(profile_name: str = "") -> str:
    clean_name = _clean_profile_name(profile_name)
    if clean_name:
        return f"Best regards,\n{clean_name}"
    return "Best regards,"


def _target_length(request: str, styles: tuple[str, ...]) -> str:
    lowered = request.lower()
    if any(marker in lowered for marker in ("brief", "short", "quick", "briefly")):
        return "brief"
    if any(marker in lowered for marker in ("detailed", "detailed email", "full update", "timeline", "milestone", "proposal", "research plan", "comprehensive")):
        return "detailed"
    if any(marker in lowered for marker in ("academic", "professor", "supervisor", "thesis", "course", "assignment", "seminar")):
        return "normal"
    return "normal"


def _generate(request: str, purpose: str, tone: str, styles: tuple[str, ...], profile_name: str = "") -> tuple[str, str]:
    generated = _llm_generation(request, purpose, tone, styles, profile_name)
    if generated is not None:
        return generated
    subject = _fallback_subject(purpose, styles)
    body = _fallback_body(purpose, tone, styles, profile_name=profile_name, request=request)
    return subject, body


def _llm_generation(request: str, purpose: str, tone: str, styles: tuple[str, ...], profile_name: str = "") -> tuple[str, str] | None:
    profile = _clean_profile_name(profile_name)
    prompt = (
        "Draft an English email from the user's request. Return JSON only with string keys "
        "subject and body. Keep it professional and natural. Use 2-3 short paragraphs for normal emails; "
        "do not write a one-sentence intro followed immediately by a closing. "
        "Target length: 60-90 words for brief emails, 90-140 words for normal professional/academic emails, "
        "and 120-180 words when the request is detailed. "
        "Do not invent dates, names, achievements, commitments, excuses, deadlines, reasons, availability, or project details "
        "that are not explicitly present in the request. Do not offer to meet or state availability unless the request explicitly asks for a meeting or timing. "
        "If important information is missing, keep the wording generic. "
        f"Requested style: {', '.join(styles) or tone}. Purpose: {purpose}. User request: {request}. "
        f"If a sender name is available, sign the email with '{profile}' instead of [Your Name]. "
        "If no name is available, use a neutral closing without inventing a name."
    )
    try:
        result = complete_llm(prompt, language_style="english", context="Email drafting only; do not send or mutate Gmail.")
        if result is None:
            return None
        data = json.loads(result.answer)
        if not isinstance(data, dict) or not isinstance(data.get("subject"), str) or not isinstance(data.get("body"), str):
            return None
        clean_subject = data["subject"].strip()
        clean_body = data["body"].strip()
        if clean_subject and clean_body and "[Your Name]" not in clean_body:
            return clean_subject, clean_body
    except (Exception, json.JSONDecodeError):
        return None
    return None


def _fallback_subject(purpose: str, styles: tuple[str, ...]) -> str:
    lowered = purpose.lower()
    if "late" in lowered and ("submission" in lowered or "project" in lowered):
        return "Late Project Submission"
    if "class" in lowered and ("missed" in lowered or "absent" in lowered):
        return "Apology"
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
    summary = " ".join(words[:8]).rstrip(".")
    return summary.capitalize() if summary else "Email Request"


def _fallback_body(purpose: str, tone: str, styles: tuple[str, ...], *, request: str = "", profile_name: str = "") -> str:
    lowered = purpose.lower()
    greeting = "Dear Professor," if "academic" in styles or "professor" in lowered else "Hello,"
    tier = _target_length(request or purpose, styles)
    closing = _closing_line(profile_name)

    if "extension" in lowered:
        body = (
            f"{greeting}\n\n"
            "I am writing to request a brief extension for the paper and would appreciate your guidance on the next steps. "
            "I understand the importance of meeting deadlines and would be grateful for your consideration and any advice on the best way to proceed.\n\n"
            "If needed, I can share additional details or provide a brief update on my progress. I would appreciate any clarification you think would be helpful.\n\n"
            "Thank you for your time and consideration. I appreciate your guidance and will follow any direction you provide.\n\n"
            f"{closing}"
        )
    elif "late" in lowered and ("submission" in lowered or "project" in lowered):
        body = (
            f"{greeting}\n\n"
            "I sincerely apologize for the delay in submitting my project. I understand the importance of meeting deadlines and appreciate your understanding.\n\n"
            "I would be grateful if you would accept my late submission and let me know whether there are any additional steps I should take.\n\n"
            "Thank you for your time and consideration. I appreciate your guidance and will follow any direction you provide.\n\n"
            f"{closing}"
        )
    elif "class" in lowered and ("missed" in lowered or "absent" in lowered):
        body = (
            f"{greeting}\n\n"
            "I apologize for missing today's class. I understand that material was covered, and I would appreciate any guidance on the key points.\n\n"
            "I would be grateful for any advice on what I should review to catch up and whether there are steps I should take next. Thank you for your understanding and your time.\n\n"
            f"{closing}"
        )
    elif "payment" in lowered or "remind" in lowered:
        body = (
            f"{greeting}\n\n"
            "I am writing to kindly remind you about the payment and to confirm the timing of the next step. Could you please arrange the payment at your earliest convenience?\n\n"
            "I would be grateful for any update you can share and will be glad to provide any information needed to move this forward.\n\n"
            f"{closing}"
        )
    elif "meeting" in lowered or "confirm" in lowered:
        body = (
            f"{greeting}\n\n"
            "I am writing to confirm tomorrow's meeting at 10 AM. I wanted to check that this time remains convenient and to confirm the plan for our discussion.\n\n"
            "Please let me know if there are any changes or if you would prefer to adjust the schedule. I would appreciate your guidance.\n\n"
            f"{closing}"
        )
    elif "follow-up" in lowered or "follow up" in lowered or "proposal" in lowered:
        body = (
            f"{greeting}\n\n"
            "I am following up regarding the proposal and would appreciate any update when convenient. I would be grateful for your guidance on the next steps and any feedback you may have.\n\n"
            "Thank you for your time and consideration. I appreciate your attention to this matter and would welcome any information that would help move things forward.\n\n"
            f"{closing}"
        )
    elif "delay" in lowered:
        body = (
            f"{greeting}\n\n"
            "I am writing to provide an update regarding the project delay. The project is delayed, and I wanted to keep you informed while I work through the next steps.\n\n"
            "I would appreciate any guidance or further information you may have, and I will share any updates as soon as they are available. Thank you for your understanding.\n\n"
            f"{closing}"
        )
    elif "request" in lowered or "assistance" in lowered or "guidance" in lowered:
        body = (
            f"{greeting}\n\n"
            f"I am writing to request your assistance regarding {purpose}. I would appreciate any guidance or clarification that would help me proceed appropriately.\n\n"
            "If needed, I can provide additional context. Thank you for your time and consideration.\n\n"
            f"{closing}"
        )
    elif tier == "brief":
        body = (
            f"{greeting}\n\n"
            f"Thank you for your time. I am following up regarding {purpose} and would appreciate your guidance on the next step. "
            "I have reviewed the current situation and would be grateful for any advice or clarification that would help move this forward.\n\n"
            "Please let me know if you need any additional information from me. If needed, I can provide additional context.\n\n"
            f"{closing}"
        )
    elif tier == "detailed":
        body = (
            f"{greeting}\n\n"
            f"I hope you are well. I am writing regarding {purpose} and would appreciate your feedback on the current status and the most suitable next step. "
            "The main priority is to keep the matter moving forward while making sure the relevant information and expectations are clear. I would also value any feedback on the main risk points and any adjustments that would help move this along.\n\n"
            "I can share any supporting details if needed. I would be grateful for your guidance and for any direction you think would be most useful.\n\n"
            "Thank you for your time and consideration. I appreciate your perspective and will be glad to follow up on any recommendations you share.\n\n"
            f"{closing}"
        )
    else:
        body = (
            f"{greeting}\n\n"
            f"I hope you are well. I am writing regarding {purpose} and would appreciate your guidance on the next step. "
            "I would be grateful for any clarification or direction that would help me proceed appropriately.\n\n"
            "At this stage, I would value your perspective and any information that would help me understand the best way to move forward. "
            "If needed, I can provide additional context.\n\n"
            "Thank you for your time and consideration. I appreciate your attention to this matter and look forward to your guidance.\n\n"
            f"{closing}"
        )

    if "[Your Name]" in body:
        body = body.replace("[Your Name]", "")
    return body.strip()
