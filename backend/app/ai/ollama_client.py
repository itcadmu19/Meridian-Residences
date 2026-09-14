"""Thin sync HTTP client for a local Ollama server (no API key required)."""

import json

import httpx

from app.core.config import settings


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
        response = httpx.post(f"{settings.ollama_base_url}/api/generate", json=payload, timeout=60.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise OllamaError(f"Ollama request failed: {exc}") from exc

    raw_text = response.json().get("response", "")
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise OllamaError(f"Ollama did not return valid JSON: {raw_text!r}") from exc
