from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import httpx


@dataclass
class OllamaClient:
    host: str
    model: str
    timeout_s: float = 120.0

    def chat(self, messages: List[Dict[str, str]]) -> str:
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

    def list_models(self) -> List[str]:
        """
        GET /api/tags returns locally available models. :contentReference[oaicite:8]{index=8}
        """
        url = f"{self.host.rstrip('/')}/api/tags"
        with httpx.Client(timeout=self.timeout_s) as client:
            r = client.get(url)
            r.raise_for_status()
            data = r.json()
        models = data.get("models") or []
        names: List[str] = []
        for m in models:
            name = m.get("name")
            if isinstance(name, str):
                names.append(name)
        return names

    def healthcheck(self) -> Tuple[bool, str]:
        """
        Basic reachability check by calling /api/tags. :contentReference[oaicite:9]{index=9}
        """
        try:
            _ = self.list_models()
            return True, "OK"
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"
