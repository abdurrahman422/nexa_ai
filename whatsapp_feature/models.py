from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Result:
    status: str
    message: str
    retryable: bool = False
    message_id: str = ''


class BeforeSendError(Exception):
    """A failure known to occur before the durable click boundary."""
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def normalize_phone(value):
    if not isinstance(value, str) or not re.fullmatch(r'\+?[0-9 ()-]+', value.strip()):
        raise ValueError('Use a phone number, not a name, group or URL.')
    digits = re.sub(r'[^0-9]', '', value)
    if digits.startswith('00'):
        digits = digits[2:]
    if re.fullmatch(r'01[3-9][0-9]{8}', digits):
        digits = '88' + digits
    if not re.fullmatch(r'[1-9][0-9]{7,14}', digits):
        raise ValueError('Use a valid international number or Bangladesh mobile number.')
    return digits


def validate_request(request_id, phone, text):
    if not isinstance(request_id, str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}', request_id):
        raise ValueError('A stable request ID (1–128 letters, numbers, . _ : -) is required.')
    phone = normalize_phone(phone)
    if not isinstance(text, str) or not text.strip() or len(text) > 10000:
        raise ValueError('Message must contain 1–10,000 characters.')
    if any((ord(c) < 32 and c not in '\n\t') or '\ue000' <= c <= '\uf8ff' for c in text):
        raise ValueError('Message contains unsupported control or WebDriver key characters.')
    if '\t' in text:
        raise ValueError('Replace tabs with spaces before sending.')
    return phone
