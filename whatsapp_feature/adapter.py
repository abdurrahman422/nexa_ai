"""Opt-in runtime binding; leaves all existing source files unchanged."""
from .browser import BrowserPool
from .models import Result
from .service import Sender
import re


def install(root):
    from app.chat import service as chat_service
    from app.permissions import store as permissions
    from app.productivity.registry import SKILLS
    from app.tools.whatsapp_sender import WhatsAppSendResult

    pool = BrowserPool(root / 'chrome-profile')
    sender = Sender(root, pool)
    original_parse = chat_service._parse_whatsapp_draft
    original_compose = chat_service._local_compose_whatsapp_draft

    def compose(contact, raw_message, tone, exact=False):
        return raw_message if exact else original_compose(contact, raw_message, tone, exact)

    def parse(message):
        intent = original_parse(message)
        if not intent.send_requested:
            return intent
        # Existing parser collapses newlines and can invoke an LLM on long sends.
        # For these explicitly supported send forms, preserve the supplied body.
        patterns = (
            r'(?is)send\s+(?:a\s+)?whatsapp\s+message\s+to\s+(?P<recipient>[^\n]+?)\s+(?:saying|that)\s+(?P<text>.+)',
            r'(?is)whatsapp\s+e\s+(?P<recipient>[^\n]+?)\s+ke\s+(?:message\s+pathao|pathao|send\s+koro|send)\s*:\s*(?P<text>.+)',
            r'(?is)(?P<recipient>[^\n]+?)কে\s+হো[য়য়]া?টসঅ্যাপে?\s+মেসেজ\s+পাঠাও\s*:\s*(?P<text>.+)',
            r'(?is)(?P<recipient>[^\n]+?)কে\s+(?:হোয়াটসঅ্যাপে|হোয়াটসঅ্যাপে)\s+মেসেজ\s+পাঠাও\s*:\s*(?P<text>.+)',
        )
        for pattern in patterns:
            match = re.fullmatch(pattern, message.strip())
            if match:
                intent.recipient = match['recipient'].strip()
                intent.raw_message = match['text']
                intent.exact = True
                return intent
        # Preserve other draft behavior, but never guess an exact send body.
        intent.send_requested = False
        return intent

    def send(request_id, phone, text):
        result = sender.send(request_id, phone, text,
                             enabled=permissions.is_permission_enabled('whatsapp_send_skill'))
        # Existing UI recognizes submitted as an executed action. Keep the honest,
        # richer result in message/detail and the durable ledger.
        if result.status in {'submitted', 'sent', 'delivered', 'read'}:
            status = 'submitted'
        elif result.status in {'login_required', 'unknown', 'wrong_chat'}:
            status = result.status
        else:
            status = 'failed'
        return WhatsAppSendResult(status, result.message, result.status)

    chat_service.send_whatsapp_message = send
    chat_service._parse_whatsapp_draft = parse
    chat_service._local_compose_whatsapp_draft = compose
    permissions.TOGGLEABLE_PERMISSIONS['whatsapp_draft_skill']['description'] = 'Prepare WhatsApp drafts. Draft commands never click Send.'
    permissions.TOGGLEABLE_PERMISSIONS['trusted_whatsapp_draft_auto_open']['description'] = 'Open draft links without extra confirmation; the user sends drafts manually.'
    permissions.TOGGLEABLE_PERMISSIONS['whatsapp_send_skill']['description'] = 'Explicit text-send commands only, through a dedicated visible browser. Exact recipient and message checks; no automatic retry after a possible send.'
    permissions.LOCKED_PERMISSIONS['auto_send_messaging']['description'] = 'Unsolicited/background messaging is locked. Explicit WhatsApp text-send has its own permission.'
    permissions.LOCKED_PERMISSIONS['auto_send_messaging']['label'] = 'Background / Unsolicited Messaging'
    for index, row in enumerate(SKILLS):
        if row[0] == 'whatsapp':
            SKILLS[index] = (row[0], row[1], row[2], 'Drafts and permission-gated explicit text sending. Live delivery testing remains required.')
    return sender, pool
