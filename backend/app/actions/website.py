"""Safe website whitelist and URL normalizer."""

from __future__ import annotations

ALLOWED_WEBSITES: dict[str, str] = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "github": "https://github.com",
    "facebook": "https://www.facebook.com",
    "gmail": "https://mail.google.com",
    "chatgpt": "https://chatgpt.com",
    "stackoverflow": "https://stackoverflow.com",
}

ALLOWED_DOMAINS: dict[str, str] = {
    "google.com": "https://www.google.com",
    "www.google.com": "https://www.google.com",
    "youtube.com": "https://www.youtube.com",
    "www.youtube.com": "https://www.youtube.com",
    "github.com": "https://github.com",
    "www.github.com": "https://github.com",
    "facebook.com": "https://www.facebook.com",
    "www.facebook.com": "https://www.facebook.com",
    "mail.google.com": "https://mail.google.com",
    "chatgpt.com": "https://chatgpt.com",
    "www.chatgpt.com": "https://chatgpt.com",
    "stackoverflow.com": "https://stackoverflow.com",
    "www.stackoverflow.com": "https://stackoverflow.com",
}

BLOCKED_URL_SCHEMES: list[str] = [
    "javascript:",
    "file:",
    "data:",
    "powershell:",
    "cmd:",
    "shell:",
]

BANGLA_ALIASES: dict[str, str] = {
    "ইউটিউব": "youtube",
    "গুগল": "google",
    "ফেসবুক": "facebook",
    "জিমেইল": "gmail",
}

PREFIXES_TO_STRIP: list[str] = [
    "open koro",
    "open",
    "website",
    "site",
    "খুলুন",
    "খুলো",
]


def normalize_website_key(value: str | None) -> str:
    if value is None:
        return ""

    key = value.strip().lower()

    for prefix in PREFIXES_TO_STRIP:
        if key.startswith(prefix):
            suffix = key[len(prefix) :].strip()
            if not suffix:
                return ""
            key = suffix

    key = " ".join(key.split())

    key = key.replace(". ", ".").replace(" .", ".")

    for raw, canonical in BANGLA_ALIASES.items():
        if raw in key:
            key = key.replace(raw, canonical)

    if key == "you tube":
        key = "youtube"

    return key


def is_blocked_url(value: str | None) -> bool:
    if not value:
        return True
    trimmed = value.strip().lower()
    for scheme in BLOCKED_URL_SCHEMES:
        if trimmed.startswith(scheme):
            return True
    return False


def get_allowed_website_url(
    value: str | None,
) -> tuple[bool, str | None, str]:
    if is_blocked_url(value) or not value:
        return (False, None, "Website target is empty or blocked.")

    key = normalize_website_key(value)

    if key in ALLOWED_WEBSITES:
        return (True, ALLOWED_WEBSITES[key], "Website is allowed.")

    if key in ALLOWED_DOMAINS:
        return (True, ALLOWED_DOMAINS[key], "Website is allowed.")

    return (False, None, "Website is not in the allowed whitelist.")


def list_allowed_websites() -> list[dict[str, str]]:
    return [{"key": k, "url": v} for k, v in ALLOWED_WEBSITES.items()]
