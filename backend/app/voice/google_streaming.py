"""Optional Google Cloud streaming STT bridge for the local Nexa frontend."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import queue
import threading
from pathlib import Path
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect


def google_streaming_status() -> dict[str, Any]:
    dependency = importlib.util.find_spec("google.cloud.speech") is not None
    enabled = os.getenv("NEXA_GOOGLE_STT_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    credentials = bool(credentials_path and Path(credentials_path).is_file())
    configured = enabled and credentials
    return {
        "ready": dependency and configured,
        "dependency_installed": dependency,
        "configured": configured,
        "enabled": enabled,
        "credentials_found": credentials,
        "internet_required": True,
        "action": "Ready when online." if dependency and configured else "Set NEXA_GOOGLE_STT_ENABLED=true and GOOGLE_APPLICATION_CREDENTIALS to a local service-account JSON file.",
    }


async def handle_google_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    status = google_streaming_status()
    if not status["ready"]:
        await websocket.send_json({"type": "unavailable", "message": status["action"]})
        await websocket.close(code=1013)
        return
    try:
        from google.cloud import speech
    except ImportError:
        await websocket.send_json({"type": "unavailable", "message": "Google Cloud Speech dependency is not installed."})
        await websocket.close(code=1013)
        return

    try:
        payload = json.loads(await websocket.receive_text())
        language = str(payload.get("language", "bn-BD"))
        sample_rate = max(8_000, min(48_000, int(payload.get("sample_rate", 48_000))))
    except (ValueError, json.JSONDecodeError):
        await websocket.send_json({"type": "error", "message": "Invalid Google STT stream configuration."})
        await websocket.close(code=1003)
        return

    audio: queue.Queue[bytes | None] = queue.Queue(maxsize=64)
    loop = asyncio.get_running_loop()
    closed = threading.Event()

    def send(message: dict[str, Any]) -> None:
        if not closed.is_set():
            asyncio.run_coroutine_threadsafe(websocket.send_json(message), loop)

    def requests():
        while True:
            chunk = audio.get()
            if chunk is None:
                break
            yield speech.StreamingRecognizeRequest(audio_content=chunk)

    def recognize() -> None:
        try:
            client = speech.SpeechClient()
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=sample_rate,
                language_code=language,
                model="latest_short",
                enable_automatic_punctuation=True,
            )
            streaming = speech.StreamingRecognitionConfig(config=config, interim_results=True, single_utterance=False)
            for response in client.streaming_recognize(config=streaming, requests=requests()):
                for result in response.results:
                    if result.alternatives:
                        alternative = result.alternatives[0]
                        send({"type": "final" if result.is_final else "interim", "text": alternative.transcript.strip(), "confidence": float(alternative.confidence or 0)})
        except Exception as exc:
            send({"type": "error", "message": f"Google streaming STT failed: {exc}"})

    threading.Thread(target=recognize, name="nexa-google-stt", daemon=True).start()
    await websocket.send_json({"type": "ready", "engine": "google_cloud", "language": language, "sample_rate": sample_rate})
    try:
        while True:
            chunk = await websocket.receive_bytes()
            try:
                audio.put_nowait(chunk)
            except queue.Full:
                _ = audio.get_nowait()
                audio.put_nowait(chunk)
    except WebSocketDisconnect:
        pass
    finally:
        closed.set()
        try:
            audio.put_nowait(None)
        except queue.Full:
            _ = audio.get_nowait()
            audio.put_nowait(None)
