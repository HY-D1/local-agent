from pathlib import Path

from local_agent.context import RepoContext


def test_select_relevant_files_filename_fallback(tmp_path: Path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    (repo / "src").mkdir()
    (repo / "src" / "database.py").write_text("x=1", encoding="utf-8")
    (repo / "src" / "auth.py").write_text("x=2", encoding="utf-8")
    (repo / "README.md").write_text("hello", encoding="utf-8")

    monkeypatch.chdir(repo)
    ctx = RepoContext.from_cwd()

    # force filename fallback by using a query that likely won't be found by rg
    results = ctx.select_relevant_files("database", max_files=10, extra_excludes=set())
    assert any("database.py" in r for r in results)
