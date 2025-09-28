"""
repo_fetcher.py

Purpose:
- Fetch metadata from a GitHub repository or local path for HuntLens to analyze.
- Used to handle attacker repos, suspicious tools, or SOC-related projects.

Functionality:
- Shallow clone a GitHub repo or scan a local directory.
- Extract README content (if any).
- Collect a list of files with short text samples (skip binaries/large files).
- Return results in a safe structured dict:
  {
    "url": "...",
    "readme": "...",
    "files": [{"path": "...", "sample": "..."}]
  }

Safety:
- Never execute repo code.
- Skip files >1MB or suspected binaries.
- Ensure UTF-8 safe output.
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Union
import mimetypes

try:
    from git import Repo
except ImportError:
    Repo = None  # Graceful fallback if GitPython is missing

def is_binary_file(filepath: str) -> bool:
    """
    Heuristically determine if the file is binary.
    """
    try:
        with open(filepath, "rb") as f:
            chunk = f.read(8192)
            if b"\0" in chunk:
                return True
            mime_type, _ = mimetypes.guess_type(filepath)
            if mime_type and (
                mime_type.startswith("image") or
                mime_type.startswith("audio") or
                mime_type.startswith("video") or
                mime_type in ["application/pdf", "application/zip"]
            ):
                return True
        return False
    except Exception:
        return True  # Treat unreadable files as binary

def safe_read_text(filepath: str, max_lines: int = 20) -> str:
    lines = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                lines.append(line.rstrip("\n"))
        return "\n".join(lines)
    except Exception:
        return ""

def find_readme(root: Union[str, Path]) -> Union[str, None]:
    candidates = [
        "README.md", "README.rst", "README.txt", "README",
        "readme.md", "readme.rst", "readme.txt", "readme"
    ]
    for c in candidates:
        path = Path(root) / c
        if path.exists() and path.is_file():
            return safe_read_text(str(path), max_lines=100)
    # Fallback: scan for any file with "readme" in name
    for f in Path(root).glob("*"):
        if f.is_file() and "readme" in f.name.lower():
            return safe_read_text(str(f), max_lines=100)
    return None

def collect_files_and_samples(root: Union[str, Path]) -> List[Dict[str, str]]:
    files = []
    root = Path(root)
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            fpath = Path(dirpath) / fname
            rel_path = str(fpath.relative_to(root))
            try:
                size = fpath.stat().st_size
                if size > 1_000_000:  # Skip large files (>1MB)
                    continue
                if is_binary_file(str(fpath)):
                    continue
                sample = safe_read_text(str(fpath), max_lines=20)
                files.append({
                    "path": rel_path,
                    "sample": sample
                })
            except Exception:
                continue
    return files

def fetch_repo_snapshot(url: str) -> dict:
    """
    Fetch metadata from a GitHub repository or local path for HuntLens analysis.
    Returns a dict with url, readme, and sampled text files.
    """
    result = {
        "url": url,
        "readme": None,
        "files": []
    }

    tmpdir = None
    is_github = url.startswith("http://github.com/") or url.startswith("https://github.com/")
    try:
        if is_github:
            if Repo is None:
                raise ImportError("GitPython is not installed.")
            tmpdir = tempfile.mkdtemp(prefix="repo_snapshot_")
            Repo.clone_from(url, tmpdir, depth=1)
            repo_root = tmpdir
        else:
            repo_root = url
            if not os.path.exists(repo_root):
                raise FileNotFoundError(f"Local directory not found: {repo_root}")

        readme = find_readme(repo_root)
        result["readme"] = readme if readme is not None else ""
        result["files"] = collect_files_and_samples(repo_root)
    except Exception as e:
        result["error"] = str(e)
    finally:
        if tmpdir and os.path.exists(tmpdir):
            shutil.rmtree(tmpdir, ignore_errors=True)
    return result