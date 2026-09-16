"""Thin sync HTTP client for a local Ollama server (no API key required).

Adapted from teammate feature-annapoorna's branch: her version used a flat
60s timeout, which made the "fall back to rule-based insight if Ollama
isn't running" path (invoice_insight_agent.generate_ai_insight's broad
except) take many seconds to actually fail on a machine without Ollama
installed - long enough to blow past the frontend's 8s axios timeout and
make the AI Insights card never appear. A split timeout fixes this: connect
fails fast (Ollama not listening = near-instant refusal) while a real,
running model still gets a generous read window to finish generating.
"""

import json

import httpx

from app.core.config import settings

_TIMEOUT = httpx.Timeout(connect=1.0, read=20.0, write=5.0, pool=5.0)


class OllamaError(Exception):
    pass


def generate_json(prompt: str, system: str) -> dict:
    """Calls the local Ollama /api/generate endpoint and parses the JSON response body."""
    payload = {
        "model": settings.ollama_model,
        "system": system,
        "prompt": prompt,
        "format": "json",
        "stream": False,
    }
    try:
        response = httpx.post(f"{settings.ollama_base_url}/api/generate", json=payload, timeout=_TIMEOUT)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise OllamaError(f"Ollama request failed: {exc}") from exc

    raw_text = response.json().get("response", "")
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise OllamaError(f"Ollama did not return valid JSON: {raw_text!r}") from exc


def generate_text(prompt: str, system: str) -> str:
    """Calls the local Ollama /api/generate endpoint for a plain-text
    (non-JSON) response - used by the AI Assistant's free-form answers."""
    payload = {
        "model": settings.ollama_model,
        "system": system,
        "prompt": prompt,
        "stream": False,
    }
    try:
        response = httpx.post(f"{settings.ollama_base_url}/api/generate", json=payload, timeout=_TIMEOUT)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise OllamaError(f"Ollama request failed: {exc}") from exc

    text = response.json().get("response", "").strip()
    if not text:
        raise OllamaError("Ollama returned an empty response")
    return text
