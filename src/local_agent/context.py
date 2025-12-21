from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from .utils import find_repo_root, iter_files, is_probably_code_file, read_text_limited


@dataclass
class RepoContext:
    root: Path

    @staticmethod
    def from_cwd() -> "RepoContext":
        return RepoContext(root=find_repo_root())

    def file_tree(self, max_files: int, extra_excludes: set[str]) -> List[str]:
        files: list[str] = []
        for p in iter_files(self.root, excludes=extra_excludes):
            rel = p.relative_to(self.root).as_posix()
            files.append(rel)
            if len(files) >= max_files:
                break
        return files

    def read_file(self, rel_path: str, max_chars: int) -> Tuple[str, str]:
        p = (self.root / rel_path).resolve()
        if not p.exists() or not p.is_file():
            return rel_path, ""
        return rel_path, read_text_limited(p, max_chars=max_chars)

    def select_relevant_files(
        self,
        query: str,
        max_files: int,
        extra_excludes: set[str],
    ) -> List[str]:
        """
        Best-effort relevance:
        - if ripgrep exists, use it
        - else fallback to filename keyword match
        """
        query = query.strip()
        if not query:
            return []

        # Try ripgrep first
        try:
            rg = subprocess.run(
                ["rg", "-n", "--hidden", "--glob", "!.git/*", query, str(self.root)],
                capture_output=True,
                text=True,
                check=False,
            )
            hits: list[str] = []
            for line in rg.stdout.splitlines():
                path = line.split(":", 1)[0]
                p = Path(path)
                try:
                    rel = p.relative_to(self.root).as_posix()
                except Exception:
                    continue
                if any(part in extra_excludes for part in Path(rel).parts):
                    continue
                hits.append(rel)

            seen: set[str] = set()
            out: list[str] = []
            for h in hits:
                if h not in seen:
                    seen.add(h)
                    out.append(h)
                if len(out) >= max_files:
                    break
            return out
        except Exception:
            pass

        # Fallback: filename match
        tokens = [t.lower() for t in query.replace("/", " ").split() if t]
        candidates: list[tuple[int, str]] = []
        for p in iter_files(self.root, excludes=extra_excludes):
            if not is_probably_code_file(p):
                continue
            rel = p.relative_to(self.root).as_posix()
            rlow = rel.lower()
            score = sum(1 for t in tokens if t in rlow)
            if score > 0:
                candidates.append((score, rel))
        candidates.sort(reverse=True)
        return [rel for _, rel in candidates[:max_files]]
