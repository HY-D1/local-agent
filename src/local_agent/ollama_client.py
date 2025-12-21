from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import httpx


@dataclass
class OllamaClient:
    host: str
    model: str
    timeout_s: float = 120.0

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        Calls Ollama /api/chat and returns assistant content.
        """
        url = f"{self.host.rstrip('/')}/api/chat"
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        with httpx.Client(timeout=self.timeout_s) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
            msg = data.get("message") or {}
            return str(msg.get("content") or "")
