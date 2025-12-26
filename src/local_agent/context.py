from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from .utils import find_repo_root, iter_files, is_probably_code_file, read_text_limited

import re

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
        - if rg finds nothing (or errors), fallback to filename/path keyword match
        """
        query = query.strip()
        if not query:
            return []

        # 1) Try ripgrep first (content search)
        try:
            q = query.lower()
            tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{2,}", q)
            stop = {
                "the", "and", "or", "to", "of", "in", "on", "for", "with", "a", "an",
                "is", "are", "was", "were", "be", "does", "do", "did", "what", "where",
                "which", "how", "why", "show", "quote", "relevant", "lines", "exact",
            }
            terms = [t for t in tokens if t not in stop][:6]
            if not terms:
                terms = [q]

            cmd = ["rg", "--files-with-matches", "--hidden", "--glob", "!.git/*"]
            for t in terms:
                cmd += ["-e", t]
            cmd.append(str(self.root))

            rg = subprocess.run(cmd, capture_output=True, text=True, check=False)

            hits: list[str] = []
            for path in (rg.stdout or "").splitlines():
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

            if out:
                return out

        except Exception:
            pass

        # 2) Fallback: filename/path match (works when rg returns 0 hits)
        tokens = [t.lower() for t in query.replace("/", " ").split() if t]
        candidates: list[tuple[int, str]] = []

        for p in self.root.rglob("*"):
            if not p.is_file():
                continue

            rel = p.relative_to(self.root).as_posix()
            parts = Path(rel).parts

            # basic ignores
            if parts and parts[0] == ".git":
                continue
            if rel.startswith(("dist/", "build/")):
                continue
            if ".egg-info" in parts or "__pycache__" in parts:
                continue

            if any(part in extra_excludes for part in parts):
                continue

            rlow = rel.lower()
            nlow = p.name.lower()

            score = 0
            for t in tokens:
                if t in nlow:
                    score += 2  # filename match strongest
                elif t in rlow:
                    score += 1  # path match weaker

            if score > 0:
                candidates.append((score, rel))

        candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return [rel for _, rel in candidates[:max_files]]
