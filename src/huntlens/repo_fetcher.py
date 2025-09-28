"""
repo_fetcher.py

Purpose:
- Clone or snapshot GitHub repos (attacker tools, suspicious code, etc.) into a temp directory.
- Extract useful context (README, file listing, recent commits) for HuntLens enrichment.

Functions:
1. fetch_repo_snapshot(url: str, branch: str = "main", max_commits: int = 5) -> dict
   - Shallow clone (depth=1) into a safe temp directory.
   - Return structured metadata:
       {
         "url": str,
         "path": str,
         "readme": Optional[str],
         "files": List[str],
         "commits": List[str]
       }
   - Enforce max file size (5MB).
   - Handle errors gracefully.

2. cleanup_repo(path: str) -> None
   - Remove the temp directory.

Requirements:
- Use GitPython for cloning.
- Never execute repo code.
- Support both GitHub HTTPS/SSH URLs and local `file://` repos (for tests).
- Always clean up temp directories when done.
"""

import os
import shutil
import tempfile
from typing import Dict, List, Optional

from git import Repo, GitCommandError


def fetch_repo_snapshot(url: str, branch: str = "main", max_commits: int = 5) -> Dict:
    """
    Clone a repo shallowly and extract context.

    Args:
        url (str): Repo URL (https/ssh/file://).
        branch (str): Branch name (default: "main").
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
        ValueError: If repo cannot be cloned.
    """
    tmp_dir = tempfile.mkdtemp(prefix="huntlens_repo_")

    try:
        repo = Repo.clone_from(url, tmp_dir, branch=branch, depth=1)
    except GitCommandError as e:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise ValueError(f"Failed to clone repo: {e}")

    # Try to read README
    readme_content: Optional[str] = None
    for name in ["README.md", "readme.md", "README"]:
        path = os.path.join(tmp_dir, name)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                readme_content = f.read()
            break

    # Collect file list (skip >5MB)
    file_list: List[str] = []
    for root, _, files in os.walk(tmp_dir):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, tmp_dir)
            try:
                if os.path.getsize(full_path) <= 5 * 1024 * 1024:
                    file_list.append(rel_path)
            except OSError:
                continue

    # Get last N commit messages
    commits: List[str] = []
    try:
        commits = [c.message.strip() for c in repo.iter_commits(branch, max_count=max_commits)]
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
    Delete the temporary repo directory.
    """
    shutil.rmtree(path, ignore_errors=True)
