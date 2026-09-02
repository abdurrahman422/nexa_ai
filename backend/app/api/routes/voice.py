"""Voice API routes: STT status/readiness/engines/transcription and TTS."""

import tempfile
import asyncio
import re
from starlette.background import BackgroundTask
from fastapi.responses import FileResponse
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, WebSocket

from app.audit.event_log import record_audit_event
from app.permissions import is_permission_enabled, permission_denied_message
from app.schemas.voice import VoiceSTTReadinessResponse
from app.schemas.voice import VoiceSTTStatusResponse
from app.schemas.voice import VoiceSTTTestTranscriptionResponse
from app.schemas.voice import VoiceSTTEngineInfo
from app.schemas.voice import VoiceSTTEnginesResponse
from app.schemas.voice import VoiceTranscriptionResponse
from app.schemas.voice import TTSVoiceInfo
from app.schemas.voice import TTSStatusResponse
from app.schemas.voice import TTSSpeakRequest
from app.schemas.voice import TTSSpeakResponse
from app.schemas.voice import EdgeTTSRequest
from app.voice.stt_engines import (
    MAX_UPLOAD_BYTES,
    get_stt_engines_overview,
    is_upload_suffix_allowed,
    transcribe_audio_file,
)

router = APIRouter(prefix="/voice", tags=["voice"])


@router.websocket("/stt/google-stream")
async def google_streaming_stt(websocket: WebSocket) -> None:
    from app.voice.google_streaming import handle_google_stream

    await handle_google_stream(websocket)

EDGE_VOICES = [
    ("bn-BD-NabanitaNeural", "Bangla - Nabanita", ["bn-BD"]),
    ("bn-BD-PradeepNeural", "Bangla - Pradeep", ["bn-BD"]),
    ("en-US-AriaNeural", "English - Aria", ["en-US"]),
    ("en-US-GuyNeural", "English - Guy", ["en-US"]),
]


def _edge_tts_available() -> bool:
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        return False
    return True


@router.get("/stt/status", response_model=VoiceSTTStatusResponse)
def get_stt_status() -> VoiceSTTStatusResponse:
    return VoiceSTTStatusResponse(
        engine="google_web_speech_online",
        mode="online_service",
        enabled=is_permission_enabled("voice_stt"),
        model_path="",
        sample_rate=0,
        language="bn-BD",
        auto_start=True,
        execution_enabled=False,
        message="Always-listening online Google Web Speech STT is selected; no local model is used.",
    )


@router.get("/stt/readiness", response_model=VoiceSTTReadinessResponse)
def get_stt_readiness() -> VoiceSTTReadinessResponse:
    overview = get_stt_engines_overview()
    engine = overview["engines"][0]
    return VoiceSTTReadinessResponse(
        dependency_installed=engine["dependency_installed"],
        dependency_message=engine["message"],
        model_available=True,
        model_message="Online service selected; no local model is required.",
        ready=engine["ready"] and is_permission_enabled("voice_stt"),
        execution_enabled=False,
        message="Bangla online STT uses bn-BD and requires internet.",
    )


@router.get("/stt/test-transcription", response_model=VoiceSTTTestTranscriptionResponse)
def get_stt_test_transcription() -> VoiceSTTTestTranscriptionResponse:
    return VoiceSTTTestTranscriptionResponse(
        status="client_required",
        transcribed=False,
        text="",
        execution_enabled=False,
        message="Use the microphone test in the app for online Web Speech STT.",
        error=None,
    )


@router.get("/stt/engines", response_model=VoiceSTTEnginesResponse)
def get_stt_engines() -> VoiceSTTEnginesResponse:
    overview = get_stt_engines_overview()
    return VoiceSTTEnginesResponse(
        preferred_engine=overview["preferred_engine"],
        engines=[VoiceSTTEngineInfo(**engine) for engine in overview["engines"]],
    )


@router.post("/stt/transcribe", response_model=VoiceTranscriptionResponse)
async def transcribe_uploaded_audio(
    audio: UploadFile = File(...),
    language: str | None = None,
) -> VoiceTranscriptionResponse:
    """Transcribe one microphone utterance detected by the frontend.

    The transcript is preview-only. It is never executed as a command —
    the frontend must route it through the normal preview/confirm flow.
    """
    if not is_permission_enabled("voice_stt"):
        denied = permission_denied_message("voice_stt")
        return VoiceTranscriptionResponse(
            status="blocked", message=denied, error=denied
        )

    if not is_upload_suffix_allowed(audio.filename):
        return VoiceTranscriptionResponse(
            status="blocked",
            message="Unsupported audio format.",
            error="Only wav/webm/ogg/mp3/m4a/flac uploads are accepted.",
        )

    data = await audio.read()
    if len(data) > MAX_UPLOAD_BYTES:
        return VoiceTranscriptionResponse(
            status="blocked",
            message="Audio upload is too large.",
            error="Maximum upload size is 15 MB.",
        )
    if not data:
        return VoiceTranscriptionResponse(
            status="failed",
            message="Audio upload is empty.",
            error="No audio data received.",
        )

    suffix = Path(audio.filename or "audio.wav").suffix.lower() or ".wav"
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = Path(tmp.name)
        result = transcribe_audio_file(tmp_path, language=language)
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass

    record_audit_event(
        source="voice_stt",
        intent="transcribe_push_to_talk",
        status=result["status"],
        message=f"engine={result.get('engine')}, chars={len(result.get('text', ''))}",
    )
    return VoiceTranscriptionResponse(
        status=result["status"],
        engine=result.get("engine", "none"),
        transcribed=result["transcribed"],
        text=result["text"],
        language=result.get("language"),
        message=(
            "Transcription completed. The transcript is preview-only and was not executed."
            if result["transcribed"]
            else (result.get("error") or "Transcription did not complete.")
        ),
        warning=result.get("warning"),
        error=result.get("error"),
    )


@router.get("/tts/status", response_model=TTSStatusResponse)
def tts_status() -> TTSStatusResponse:
    available = _edge_tts_available()
    enabled = is_permission_enabled("voice_tts") and is_permission_enabled("edge_tts")
    return TTSStatusResponse(
        dependency_installed=available,
        available=available,
        enabled=enabled,
        voices=[TTSVoiceInfo(id=voice_id, name=name, languages=languages) for voice_id, name, languages in EDGE_VOICES],
        message=(
            "Online Edge neural TTS is ready."
            if available and enabled
            else "Online Edge TTS is installed but disabled in the Security Center."
            if available
            else "edge-tts is not installed."
        ),
        error=None if available else "Install edge-tts to use online neural voices.",
    )


@router.post("/tts/speak", response_model=TTSSpeakResponse)
def tts_speak(request: TTSSpeakRequest) -> TTSSpeakResponse:
    if not is_permission_enabled("voice_tts") or not is_permission_enabled("edge_tts"):
        denied = permission_denied_message("edge_tts")
        return TTSSpeakResponse(status="blocked", message=denied, error=denied)
    return TTSSpeakResponse(
        status="audio_endpoint_required",
        spoken=False,
        message="Use /voice/tts/edge/audio so the app can play online neural audio.",
        error=None,
    )


@router.get("/tts/edge/status")
def edge_tts_status() -> dict:
    return {"status": "ok", "available": _edge_tts_available(), "enabled": is_permission_enabled("edge_tts"), "voices": [voice[0] for voice in EDGE_VOICES]}


@router.post("/tts/edge/audio")
def edge_tts_audio(request: EdgeTTSRequest):
    if not is_permission_enabled("voice_tts") or not is_permission_enabled("edge_tts"):
        denied = permission_denied_message("edge_tts")
        return TTSSpeakResponse(status="blocked", message=denied, error=denied)
    if request.voice not in {voice[0] for voice in EDGE_VOICES}:
        return TTSSpeakResponse(status="blocked", message="Voice is not in the allowed Edge TTS list.", error="Unsupported voice.")
    if not re.fullmatch(r"[+-]\d{1,3}%", request.rate):
        return TTSSpeakResponse(status="blocked", message="Invalid speech rate.", error="Invalid rate.")
    try:
        import edge_tts
    except ImportError:
        return TTSSpeakResponse(status="not_ready", message="Install edge-tts first.", error="edge-tts is not installed.")
    text = request.text.strip()[:800]
    if not text:
        return TTSSpeakResponse(status="failed", message="Text is empty.", error="Text is empty.")
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp_path = Path(tmp.name); tmp.close()
    try:
        asyncio.run(edge_tts.Communicate(text, request.voice, rate=request.rate).save(str(tmp_path)))
        record_audit_event("voice_tts", "edge_tts_audio", "completed", message=f"voice={request.voice}, chars={len(text)}")
        return FileResponse(tmp_path, media_type="audio/mpeg", filename="nexa-voice.mp3", background=BackgroundTask(tmp_path.unlink, missing_ok=True))
    except Exception as exc:
        tmp_path.unlink(missing_ok=True)
        return TTSSpeakResponse(status="failed", message="Edge TTS failed.", error=str(exc))
