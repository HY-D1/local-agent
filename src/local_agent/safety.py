from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .utils import atomic_write


def backup_file(path: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = path.with_suffix(path.suffix + f".bak_{ts}")
    bak.write_text(path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
    return bak


def safe_apply(path: Path, new_content: str, make_backup: bool = True) -> None:
    if make_backup and path.exists():
        backup_file(path)
    atomic_write(path, new_content)
