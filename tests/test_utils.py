from pathlib import Path

from local_agent.utils import find_repo_root, read_text_limited


def test_find_repo_root(tmp_path: Path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    sub = repo / "a" / "b"
    sub.mkdir(parents=True)
    monkeypatch.chdir(sub)

    assert find_repo_root() == repo.resolve()


def test_read_text_limited_snips(tmp_path: Path):
    p = tmp_path / "big.txt"
    p.write_text("A" * 2000 + "B" * 2000, encoding="utf-8")

    out = read_text_limited(p, max_chars=1000)
    assert "...<snip>..." in out
    assert len(out) < 2000  # should be shortened
