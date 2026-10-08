import difflib
import subprocess
from pathlib import Path

from .artifacts import digest_bytes
from .exceptions import PipelineError


def git(root, *args):
    process = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=30)
    if process.returncode:
        raise PipelineError(f"Git inspection failed: git {' '.join(args)}: {process.stderr.strip()}")
    return process.stdout.strip()


def inspect_git(root):
    return {"head": git(root, "rev-parse", "HEAD"), "branch": git(root, "branch", "--show-current"),
            "status": git(root, "status", "--porcelain=v1"), "worktrees": git(root, "worktree", "list")}


def snapshot(root):
    """Capture actual checked-out bytes, including dirty/untracked files, excluding runtime."""
    root = Path(root)
    excluded = {".git", ".orchestrator", "__pycache__", ".venv", "node_modules", "build", "dist"}
    files = {}
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if excluded.intersection(relative.parts) or any(p.endswith(".egg-info") for p in relative.parts):
            continue
        if path.is_symlink():
            files[str(relative)] = {"symlink": str(path.readlink())}
        elif path.is_file():
            raw = path.read_bytes()
            files[str(relative)] = {"digest": digest_bytes(raw), "content": raw.decode("utf-8", errors="replace")}
    return files


def architecture_snapshot(files):
    return {path: value for path, value in files.items() if path.startswith("docs/architecture/")}


def architecture_diff(baseline, current):
    changes = []
    for path in sorted(baseline.keys() | current.keys()):
        old, new = baseline.get(path), current.get(path)
        if old == new:
            continue
        change = "added" if old is None else "deleted" if new is None else "modified"
        diff = "".join(difflib.unified_diff((old or {}).get("content", "").splitlines(True),
                                             (new or {}).get("content", "").splitlines(True),
                                             fromfile="baseline/" + path, tofile="current/" + path))
        changes.append({"path": path, "change": change, "adr": "/decisions/" in path, "diff": diff})
    return changes
