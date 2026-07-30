"""Small, server-side client for the local Ollama HTTP API.

The browser never receives the Ollama address.  This keeps the model service
private and lets the API apply CRM permissions before any data is sent to it.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
import httpx

_env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_env_path)


class OllamaUnavailable(RuntimeError):
    """Raised when the local model service cannot answer a request."""


def _base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")


def get_model_name() -> str:
    return os.getenv("OLLAMA_MODEL", "qwen3:4b")


def is_enabled() -> bool:
    return os.getenv("AI_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}


def _timeout() -> float:
    try:
        return max(5.0, float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "90")))
    except ValueError:
        return 90.0


def get_status() -> tuple[bool, str]:
    """Return whether the configured model is currently installed in Ollama."""
    if not is_enabled():
        return False, "AI Copilot has been disabled by the server administrator."

    model = get_model_name()
    try:
        with httpx.Client(timeout=min(_timeout(), 10.0)) as client:
            response = client.get(f"{_base_url()}/api/tags")
            response.raise_for_status()
    except httpx.HTTPError:
        return False, "Ollama is offline. Start the Ollama service and try again."

    models = response.json().get("models", [])
    available_names = {item.get("name") for item in models if isinstance(item, dict)}
    if model not in available_names:
        return False, f"The configured model ({model}) is not installed on this server."
    return True, "Ready — responses stay on this server."


def chat(messages: list[dict[str, str]]) -> str:
    """Generate one non-streaming assistant response from the configured model."""
    if not is_enabled():
        raise OllamaUnavailable("AI Copilot is disabled.")

    payload: dict[str, Any] = {
        "model": get_model_name(),
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.8,
            "num_predict": 150,
            "num_ctx": 1024,
        },
    }
    try:
        with httpx.Client(timeout=_timeout()) as client:
            response = client.post(f"{_base_url()}/api/chat", json=payload)
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise OllamaUnavailable("The local model took too long to respond. Please try again.") from exc
    except httpx.HTTPError as exc:
        raise OllamaUnavailable("Ollama could not complete this request. Please try again.") from exc

    content = response.json().get("message", {}).get("content", "").strip()
    if not content:
        raise OllamaUnavailable("The local model returned an empty response. Please try again.")
    return content
