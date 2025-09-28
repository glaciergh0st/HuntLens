"""
Tests for repo_fetcher.py
"""

import os
from src.huntlens.repo_fetcher import fetch_repo_snapshot


def test_fetch_local_repo_with_readme(tmp_path):
    # Setup a fake repo directory
    repo_dir = tmp_path / "fake_repo"
    repo_dir.mkdir()

    # Add a README.md
    readme_file = repo_dir / "README.md"
    readme_file.write_text("# Fake Repo\nThis is a test repo.")

    # Add a small Python file
    code_file = repo_dir / "tool.py"
    code_file.write_text("print('hello world')\n")

    # Run snapshot
    result = fetch_repo_snapshot(str(repo_dir))

    # Assertions
    assert isinstance(result, dict)
    assert result["url"] == str(repo_dir)
    assert "# Fake Repo" in result["readme"]
    assert any(f["path"].endswith("tool.py") for f in result["files"])


def test_fetch_local_repo_without_readme(tmp_path):
    repo_dir = tmp_path / "empty_repo"
    repo_dir.mkdir()

    code_file = repo_dir / "script.sh"
    code_file.write_text("echo 'hi'\n")

    result = fetch_repo_snapshot(str(repo_dir))

    assert result["readme"] is None or result["readme"] == ""
    assert "files" in result
    assert any("script.sh" in f["path"] for f in result["files"])


def test_large_file_is_skipped(tmp_path):
    repo_dir = tmp_path / "big_repo"
    repo_dir.mkdir()

    large_file = repo_dir / "big.bin"
    # Write a file >1MB
    large_file.write_bytes(b"0" * (1024 * 1024 + 1))

    result = fetch_repo_snapshot(str(repo_dir))

    # Ensure big file is not included
    assert not any("big.bin" in f["path"] for f in result["files"])
