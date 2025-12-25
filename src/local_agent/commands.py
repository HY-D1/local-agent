from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class CommandSpec:
    scope: str  # "project" | "user"
    name: str   # command name, e.g. "review"
    path: Path  # path to .md file


def _project_commands_dir(repo_root: Path) -> Path:
    return repo_root / ".local-agent" / "commands"


def _user_commands_dir() -> Path:
    return Path.home() / ".local-agent" / "commands"


def discover_commands(repo_root: Path) -> List[CommandSpec]:
    """
    Discover project + user markdown commands.
    Similar idea to Claude Code's project/user command scopes. :contentReference[oaicite:6]{index=6}
    """
    specs: List[CommandSpec] = []

    for scope, base in (("project", _project_commands_dir(repo_root)), ("user", _user_commands_dir())):
        if not base.exists():
            continue
        for p in base.rglob("*.md"):
            if not p.is_file():
                continue
            name = p.stem
            specs.append(CommandSpec(scope=scope, name=name, path=p))

    # stable sort for nicer listing
    specs.sort(key=lambda s: (s.scope, s.name))
    return specs


def index_commands(specs: List[CommandSpec]) -> Tuple[Dict[str, CommandSpec], Dict[str, List[CommandSpec]]]:
    """
    Returns:
      - unique: mapping for commands without conflicts by short name
      - all_by_name: mapping name -> [specs...]
    """
    by_name: Dict[str, List[CommandSpec]] = {}
    for s in specs:
        by_name.setdefault(s.name, []).append(s)

    unique: Dict[str, CommandSpec] = {}
    for name, lst in by_name.items():
        if len(lst) == 1:
            unique[name] = lst[0]
    return unique, by_name


def resolve_command(
    specs: List[CommandSpec],
    token: str,
) -> Optional[CommandSpec]:
    """
    token examples:
      - "review" (if unique)
      - "project:review"
      - "user:review"
    """
    token = token.strip().lstrip("/")
    if not token:
        return None

    if ":" in token:
        scope, name = token.split(":", 1)
        scope = scope.strip().lower()
        name = name.strip()
        for s in specs:
            if s.scope == scope and s.name == name:
                return s
        return None

    unique, _ = index_commands(specs)
    return unique.get(token)


def render_template(markdown_text: str, arguments: str) -> str:
    """
    Supports $ARGUMENTS replacement like Claude Code best-practices describes. :contentReference[oaicite:7]{index=7}
    """
    return markdown_text.replace("$ARGUMENTS", arguments.strip())
