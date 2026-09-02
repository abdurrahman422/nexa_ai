"""Online STT engines for Nexa AI.

The desktop continuous-listening path detects utterances locally and sends a
short WAV recording to Google Speech Recognition. No local model is loaded.
"""

from __future__ import annotations

from pathlib import Path

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
ALLOWED_UPLOAD_SUFFIXES = {".wav", ".webm", ".ogg", ".mp3", ".m4a", ".flac"}


def get_stt_engines_overview() -> dict:
    try:
        import speech_recognition  # noqa: F401
        dependency_installed = True
    except ImportError:
        dependency_installed = False
    return {
        "preferred_engine": "google_web_speech_online",
        "engines": [
            {
                "name": "google_web_speech_online",
                "label": "Google Web Speech (online, Bangla)",
                "dependency_installed": dependency_installed,
                "model_available": True,
                "ready": dependency_installed,
                "message": (
                    "Uses online recognition with bn-BD; no local model is required."
                    if dependency_installed
                    else "Install SpeechRecognition to use online Bangla STT."
                ),
            },
        ],
    }


def is_upload_suffix_allowed(filename: str | None) -> bool:
    if not filename:
        return False
    return Path(filename).suffix.lower() in ALLOWED_UPLOAD_SUFFIXES


def transcribe_audio_file(audio_path: str | Path, language: str | None = None) -> dict:
    """Transcribe a WAV recording with the online Google recognition service."""
    selected_language = language or "bn-BD"
    try:
        import speech_recognition as sr
    except ImportError:
        return {
            "status": "not_ready", "transcribed": False, "text": "",
            "language": selected_language, "engine": "google_web_speech_online",
            "error": "SpeechRecognition is not installed.",
        }

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(str(audio_path)) as source:
            audio = recognizer.record(source)
        text = str(recognizer.recognize_google(audio, language=selected_language)).strip()
    except sr.UnknownValueError:
        return {
            "status": "failed", "transcribed": False, "text": "",
            "language": selected_language, "engine": "google_web_speech_online",
            "error": "Speech was not clear enough to transcribe.",
        }
    except sr.RequestError as exc:
        return {
            "status": "failed", "transcribed": False, "text": "",
            "language": selected_language, "engine": "google_web_speech_online",
            "error": f"Online speech service request failed: {exc}",
        }
    except (OSError, ValueError, EOFError) as exc:
        return {
            "status": "failed", "transcribed": False, "text": "",
            "language": selected_language, "engine": "google_web_speech_online",
            "error": f"Audio could not be read: {exc}",
        }

    return {
        "status": "completed", "transcribed": bool(text), "text": text,
        "language": selected_language, "engine": "google_web_speech_online",
        "error": None,
    }
