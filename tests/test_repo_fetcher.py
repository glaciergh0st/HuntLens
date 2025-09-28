"""
Tests for repo_fetcher.py
"""

import os
import pytest
from src.huntlens import repo_fetcher


def test_fetch_invalid_repo():
    with pytest.raises(ValueError):
        repo_fetcher.fetch_repo_snapshot("https://github.com/not-a-real-user/not-a-real-repo")


def test_fetch_and_cleanup(tmp_path):
    # Init a tiny git repo locally
    repo_dir = tmp_path / "dummy_repo"
    repo_dir.mkdir()
    readme = repo_dir / "README.md"
    readme.write_text("# Dummy Repo")

    # Init a bare repo to simulate git
    import subprocess
    subprocess.run(["git", "init"], cwd=repo_dir, check=True)
    subprocess.run(["git", "add", "README.md"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True)

    # Clone via file://
    snapshot = repo_fetcher.fetch_repo_snapshot(f"file://{repo_dir}")
    assert snapshot["readme"] is not None
    assert "README.md" in snapshot["files"]

    # Cleanup
    repo_fetcher.cleanup_repo(snapshot["path"])
    assert not os.path.exists(snapshot["path"])
