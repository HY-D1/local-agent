from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import httpx


class OllamaError(Exception):
    """Base exception for Ollama client errors."""
    pass


class OllamaTimeoutError(OllamaError):
    """Raised when the request to Ollama times out."""
    pass


class OllamaConnectionError(OllamaError):
    """Raised when cannot connect to Ollama server."""
    pass


@dataclass
class OllamaClient:
    host: str
    model: str
    timeout_s: float = 300.0  # Increased default to 5 minutes for slower models

    def chat(self, messages: List[Dict[str, str]]) -> str:
        url = f"{self.host.rstrip('/')}/api/chat"
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                r = client.post(url, json=payload)
                r.raise_for_status()
                data = r.json()
                msg = data.get("message") or {}
                return str(msg.get("content") or "")
        except httpx.TimeoutException as e:
            raise OllamaTimeoutError(
                f"Request timed out after {self.timeout_s}s. "
                f"The model '{self.model}' may be loading or the request was too complex. "
                f"Try: 1) Wait a moment and retry, 2) Use a smaller context, or 3) Increase timeout in config."
            ) from e
        except httpx.ConnectError as e:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self.host}. "
                f"Is Ollama running? Try: ollama serve"
            ) from e
        except httpx.HTTPStatusError as e:
            raise OllamaError(
                f"Ollama API error: {e.response.status_code} - {e.response.text}"
            ) from e

    def list_models(self) -> List[str]:
        """
        GET /api/tags returns locally available models.
        """
        url = f"{self.host.rstrip('/')}/api/tags"
        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                r = client.get(url)
                r.raise_for_status()
                data = r.json()
        except httpx.TimeoutException as e:
            raise OllamaTimeoutError(
                f"Request timed out after {self.timeout_s}s. "
                f"Ollama server at {self.host} is not responding."
            ) from e
        except httpx.ConnectError as e:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self.host}. "
                f"Is Ollama running? Try: ollama serve"
            ) from e
        models = data.get("models") or []
        names: List[str] = []
        for m in models:
            name = m.get("name")
            if isinstance(name, str):
                names.append(name)
        return names

    def healthcheck(self) -> Tuple[bool, str]:
        """
        Basic reachability check by calling /api/tags.
        """
        try:
            _ = self.list_models()
            return True, "OK"
        except OllamaError as e:
            return False, str(e)
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"
