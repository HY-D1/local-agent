from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib  # py3.11+
except Exception:  # pragma: no cover
    import tomli as tomllib  # type: ignore

from .utils import find_repo_root


@dataclass
class AppConfig:
    ollama_host: str = "http://localhost:11434"
    model: str = "qwen2.5-coder:7b"
    max_file_chars: int = 120_000
    max_context_files: int = 35
    max_tree_files: int = 250
    extra_excludes: set[str] = None  # type: ignore

    def __post_init__(self) -> None:
        if self.extra_excludes is None:
            self.extra_excludes = set()


def load_config() -> AppConfig:
    """
    Loads config from (in priority order):
      1) ./.local-agent/config.toml
      2) <repo_root>/.local-agent/config.toml
    """
    cwd = Path.cwd()
    repo = find_repo_root(cwd)

    candidates = [
        cwd / ".local-agent" / "config.toml",
        repo / ".local-agent" / "config.toml",
    ]

    cfg = AppConfig()
    for f in candidates:
        if not f.exists():
            continue
        data = tomllib.loads(f.read_text(encoding="utf-8"))
        cfg.ollama_host = str(data.get("ollama_host", cfg.ollama_host))
        cfg.model = str(data.get("model", cfg.model))
        cfg.max_file_chars = int(data.get("max_file_chars", cfg.max_file_chars))
        cfg.max_context_files = int(data.get("max_context_files", cfg.max_context_files))
        cfg.max_tree_files = int(data.get("max_tree_files", cfg.max_tree_files))
        excludes = data.get("extra_excludes", [])
        if isinstance(excludes, list):
            cfg.extra_excludes = set(map(str, excludes))
        break

    return cfg
