"""
Tests for repo_fetcher.py
"""

import os
import subprocess
import pytest
from src.huntlens import repo_fetcher


@pytest.mark.skip(reason="Avoid hitting GitHub during local test runs")
def test_fetch_invalid_repo():
    # This would trigger GitHub auth prompts; skipped for local/CI safety.
    with pytest.raises(ValueError):
        repo_fetcher.fetch_repo_snapshot("https://github.com/not-a-real-user/not-a-real-repo")


def test_fetch_and_cleanup(tmp_path):
    # Create a dummy git repo locally
    repo_dir = tmp_path / "dummy_repo"
    repo_dir.mkdir()
    readme = repo_dir / "README.md"
    readme.write_text("# Dummy Repo\n\nThis is a test.")

    # Init git repo (force branch to main for test consistency)
    subprocess.run(["git", "init"], cwd=repo_dir, check=True)
    subprocess.run(["git", "branch", "-m", "main"], cwd=repo_dir, check=True)
    subprocess.run(["git", "add", "README.md"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_dir, check=True)

    # Clone it back via file://
    snapshot = repo_fetcher.fetch_repo_snapshot(f"file://{repo_dir}")
    assert snapshot["readme"] is not None
    assert "README.md" in snapshot["files"]
    assert isinstance(snapshot["commits"], list)

    # Cleanup
    repo_fetcher.cleanup_repo(snapshot["path"])
    assert not os.path.exists(snapshot["path"])
