from pathlib import Path

from local_agent.config import load_config


def test_load_config_from_repo(tmp_path: Path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    cfg_dir = repo / ".local-agent"
    cfg_dir.mkdir()
    (cfg_dir / "config.toml").write_text(
        """
ollama_host = "http://127.0.0.1:11434"
model = "test-model:latest"
max_file_chars = 123
max_context_files = 7
max_tree_files = 42
extra_excludes = ["data", "logs"]
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.chdir(repo)
    cfg = load_config()

    assert cfg.ollama_host == "http://127.0.0.1:11434"
    assert cfg.model == "test-model:latest"
    assert cfg.max_file_chars == 123
    assert cfg.max_context_files == 7
    assert cfg.max_tree_files == 42
    assert "data" in cfg.extra_excludes
    assert "logs" in cfg.extra_excludes
