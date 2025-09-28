"""
repo_fetcher.py

Purpose:
- Safely fetch and extract metadata from GitHub repos (attacker tools or otherwise).
- Provide downstream modules with README content, file inventory, and commit history.

Functions:
1. fetch_repo_snapshot(url: str, branch: str = "main", max_commits: int = 5) -> dict
    - Clone a repo shallowly into a temp directory.
    - Extract README (if available), list of files (limit 5MB each), and last N commit messages.
    - Return a structured dict.

2. cleanup_repo(path: str) -> None
    - Delete the temporary repo safely.

Safety:
- Always shallow clone (depth=1).
- Never execute repo code.
- Gracefully handle missing branch, missing README, and large files.
"""

import os
import tempfile
import shutil
from typing import Dict, List, Optional
from git import Repo, GitCommandError


def fetch_repo_snapshot(url: str, branch: str = "main", max_commits: int = 5) -> Dict:
    """
    Clone a GitHub repo shallowly and extract useful context.

    Args:
        url (str): Repo URL (https/ssh/file://).
        branch (str): Branch to checkout (default: main).
        max_commits (int): Number of commit messages to extract.

    Returns:
        dict: {
            "url": str,
            "path": str,
            "readme": Optional[str],
            "files": List[str],
            "commits": List[str]
        }

    Raises:
        ValueError: If the repo cannot be cloned or accessed.
    """
    tmp_dir = tempfile.mkdtemp(prefix="huntlens_repo_")

    # Try branch first, fallback to default
    try:
        repo = Repo.clone_from(url, tmp_dir, branch=branch, depth=1)
    except GitCommandError:
        try:
            repo = Repo.clone_from(url, tmp_dir, depth=1)  # let Git pick default branch
        except GitCommandError as e:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            raise ValueError(f"Failed to clone repo: {e}")

    # Try to extract README
    readme_content = None
    for name in ["README.md", "readme.md", "README"]:
        path = os.path.join(tmp_dir, name)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                readme_content = f.read()
            break

    # Collect small file paths
    file_list: List[str] = []
    for root, _, files in os.walk(tmp_dir):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, tmp_dir)
            try:
                if os.path.getsize(full_path) <= 5 * 1024 * 1024:  # 5MB max
                    file_list.append(rel_path)
            except OSError:
                continue

    # Get last N commits (may fail if no history)
    commits = []
    try:
        commits = [c.message.strip() for c in repo.iter_commits(max_count=max_commits)]
    except Exception:
        pass

    return {
        "url": url,
        "path": tmp_dir,
        "readme": readme_content,
        "files": file_list,
        "commits": commits,
    }


def cleanup_repo(path: str) -> None:
    """
    Remove the temporary repo directory.
    """
    shutil.rmtree(path, ignore_errors=True)
