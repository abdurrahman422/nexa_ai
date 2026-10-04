from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


project_root = Path(SPECPATH).resolve().parent
hiddenimports = collect_submodules("app") + [
    "whatsapp_feature.adapter",
    "whatsapp_feature.browser",
    "whatsapp_feature.ledger",
    "whatsapp_feature.models",
    "whatsapp_feature.service",
    "selenium.common.exceptions",
    "selenium.webdriver",
    "selenium.webdriver.chrome.options",
    "selenium.webdriver.chrome.service",
    "selenium.webdriver.chrome.webdriver",
    "selenium.webdriver.common.action_chains",
    "selenium.webdriver.common.by",
    "selenium.webdriver.common.keys",
    "selenium.webdriver.support.ui",
]

a = Analysis(
    ["run_backend.py"],
    pathex=[".", str(project_root)],
    binaries=[],
    datas=[(".env.example", ".")],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "tkinter"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="nexa-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="nexa-backend",
)
