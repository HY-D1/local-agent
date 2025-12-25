from pathlib import Path

from local_agent.safety import safe_apply


def test_safe_apply_creates_backup(tmp_path: Path):
    p = tmp_path / "file.py"
    p.write_text("old", encoding="utf-8")

    safe_apply(p, "new", make_backup=True)

    assert p.read_text(encoding="utf-8") == "new"
    backups = list(tmp_path.glob("file.py.bak_*"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "old"
