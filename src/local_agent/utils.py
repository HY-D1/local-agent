from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable


DEFAULT_EXCLUDES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".idea",
    ".vscode",
}


CODE_EXTS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".kt", ".go", ".rs", ".cpp", ".c",
    ".cs", ".rb", ".php", ".swift", ".scala", ".sql", ".sh", ".zsh", ".yaml", ".yml",
    ".toml", ".json", ".md",
}


def find_repo_root(start: Path | None = None) -> Path:
    start = start or Path.cwd()
    cur = start.resolve()
    for _ in range(50):
        if (cur / ".git").exists():
            return cur
        if cur.parent == cur:
            return start.resolve()
        cur = cur.parent
    return start.resolve()


def is_probably_code_file(path: Path) -> bool:
    return path.suffix.lower() in CODE_EXTS


def iter_files(root: Path, excludes: set[str] | None = None) -> Iterable[Path]:
    excludes = excludes or set()
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        parts = set(p.parts)
        if parts.intersection(DEFAULT_EXCLUDES | excludes):
            continue
        yield p


def read_text_limited(path: Path, max_chars: int) -> str:
    try:
        data = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    if len(data) <= max_chars:
        return data
    head = data[: max_chars // 2]
    tail = data[-max_chars // 2 :]
    return head + "\n\n...<snip>...\n\n" + tail


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)
