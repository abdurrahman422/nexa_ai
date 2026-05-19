"""Safe Windows app whitelist config and alias normalizer."""

from __future__ import annotations

ALLOWED_APPS: dict[str, dict[str, str]] = {
    "notepad": {"command": "notepad", "label": "Notepad"},
    "calculator": {"command": "calc", "label": "Calculator"},
    "chrome": {"command": "chrome", "label": "Google Chrome"},
    "file_explorer": {"command": "explorer", "label": "File Explorer"},
    "vscode": {"command": "code", "label": "Visual Studio Code"},
}

BLOCKED_APP_KEYWORDS: list[str] = [
    "cmd",
    "command prompt",
    "powershell",
    "regedit",
    "registry",
    "taskmgr",
    "task manager",
    "control panel",
    "gpedit",
    "services",
    "system32",
    "shutdown",
    "restart",
    "format",
    "delete",
    "ডিলিট",
    "ফরম্যাট",
    "শাটডাউন",
    "রিস্টার্ট",
]

PREFIX_WORDS: list[str] = [
    "open",
    "app",
    "software",
    "launch",
    "run",
    "kholo",
    "khulo",
    "chalao",
    "চালাও",
    "খোলো",
    "খুলুন",
]

ALIAS_MAP: dict[str, str] = {
    "note pad": "notepad",
    "নোটপ্যাড": "notepad",
    "calc": "calculator",
    "ক্যালকুলেটর": "calculator",
    "chrome browser": "chrome",
    "google chrome": "chrome",
    "ক্রোম": "chrome",
    "file explorer": "file_explorer",
    "explorer": "file_explorer",
    "files": "file_explorer",
    "ফাইল": "file_explorer",
    "vs code": "vscode",
    "vscode": "vscode",
    "visual studio code": "vscode",
}


def normalize_app_key(value: str | None) -> str:
    if value is None:
        return ""

    key = value.strip().lower()
    key = " ".join(key.split())

    for prefix in PREFIX_WORDS:
        if key.startswith(prefix):
            suffix = key[len(prefix) :].strip()
            if suffix:
                key = suffix
                break

    for raw, canonical in ALIAS_MAP.items():
        if key == raw:
            return canonical

    return key


def is_blocked_app_request(value: str | None) -> bool:
    if not value:
        return True
    normalized = value.strip().lower()
    normalized = " ".join(normalized.split())
    for keyword in BLOCKED_APP_KEYWORDS:
        if keyword in normalized:
            return True
    return False


def get_allowed_app(
    value: str | None,
) -> tuple[bool, dict[str, str] | None, str]:
    if is_blocked_app_request(value) or not value:
        return (False, None, "App target is empty or blocked.")

    key = normalize_app_key(value)

    if key in ALLOWED_APPS:
        return (True, dict(ALLOWED_APPS[key]), "App is allowed.")

    return (False, None, "App is not in the allowed whitelist.")


def list_allowed_apps() -> list[dict[str, str]]:
    return [
        {"key": k, "command": v["command"], "label": v["label"]}
        for k, v in ALLOWED_APPS.items()
    ]
