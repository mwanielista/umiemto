import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path

from .config import safe_path
from .exceptions import ConcurrencyError, PipelineError
from .models import PipelineState, Stage, now


EDGES = {
    Stage.BUSINESS_ANALYSIS: {Stage.BA_APPROVAL},
    Stage.BA_APPROVAL: {Stage.SYSTEM_ANALYSIS},
    Stage.SYSTEM_ANALYSIS: {Stage.SA_APPROVAL},
    Stage.SA_APPROVAL: {Stage.ARCHITECTURE},
    Stage.ARCHITECTURE: {Stage.ARCHITECTURE_REVIEW},
    Stage.ARCHITECTURE_REVIEW: {
        Stage.ARCH_FIX,
        Stage.ARCH_VALIDATION,
        Stage.HUMAN_REQUIRED,
    },
    Stage.ARCH_FIX: {Stage.ARCHITECTURE_REVIEW},
    Stage.ARCH_VALIDATION: {Stage.DONE},
}

TERMINALS = {
    Stage.DONE,
    Stage.BLOCKED,
    Stage.FAILED,
    Stage.HUMAN_REQUIRED,
}


def atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".pending-")

    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())

        os.replace(name, path)

        dir_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def write_json(path, value):
    atomic_write(
        path,
        (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode(),
    )


class StateStore:
    def __init__(self, root):
        self.directory = Path(root) / ".orchestrator"
        self.path = self.directory / "state.json"

    @contextmanager
    def lock(self):
        root = self.directory.parent
        safe_path(root, ".orchestrator/lock")
        self.directory.mkdir(parents=True, exist_ok=True)

        with (self.directory / "lock").open("a+") as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise ConcurrencyError(
                    "Another factory instance controls this worktree"
                ) from error

            try:
                yield
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    def load(self):
        safe_path(self.directory.parent, ".orchestrator/state.json")

        if not self.path.exists():
            return None

        try:
            state = PipelineState(**json.loads(self.path.read_text()))
            Stage(state.stage)

            if state.status not in {
                "PENDING",
                "RUNNING",
                "WAITING_FOR_APPROVAL",
                "DONE",
                "BLOCKED",
                "FAILED",
                "HUMAN_REQUIRED",
                "STALE",
            }:
                raise ValueError("Invalid status")

            if type(state.attempt) is not int or not 1 <= state.attempt <= 3:
                raise ValueError("Invalid review attempt")

            if (
                state.stage
                in {Stage.BLOCKED, Stage.FAILED, Stage.HUMAN_REQUIRED}
                and not state.reason
            ):
                raise ValueError("Terminal failure requires a reason")

            if not state.run_id or Path(state.run_id).name != state.run_id:
                raise ValueError("Invalid run ID")

            return state
        except (OSError, ValueError, TypeError) as error:
            raise PipelineError(f"Invalid persisted state: {error}") from error

    def run_dir(self, state):
        return safe_path(
            self.directory.parent,
            f".orchestrator/runs/{state.run_id}",
        )

    def event(self, state, kind, **details):
        path = safe_path(
            self.directory.parent,
            f".orchestrator/runs/{state.run_id}/events.jsonl",
        )
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("a") as stream:
            stream.write(
                json.dumps(
                    {
                        "timestamp": now(),
                        "stage": state.stage,
                        "attempt": state.attempt,
                        "event": kind,
                        **details,
                    }
                )
                + "\n"
            )
            stream.flush()
            os.fsync(stream.fileno())

    def save(self, state):
        safe_path(self.directory.parent, ".orchestrator/state.json")
        state.updated_at = now()

        write_json(self.path, asdict(state))
        write_json(self.run_dir(state) / "run.json", asdict(state))

    def transition(self, state, target, reason=None):
        source = Stage(state.stage)
        target = Stage(target)

        allowed = EDGES.get(source, set()) | (
            {
                Stage.BLOCKED,
                Stage.FAILED,
                Stage.HUMAN_REQUIRED,
            }
            if source not in TERMINALS
            else set()
        )

        if target not in allowed:
            raise PipelineError(f"Invalid transition: {source} -> {target}")

        if (
            target
            in {Stage.BLOCKED, Stage.FAILED, Stage.HUMAN_REQUIRED}
            and not reason
        ):
            raise PipelineError(f"{target} requires a reason")

        state.stage = target
        state.status = (
            "WAITING_FOR_APPROVAL"
            if target in {Stage.BA_APPROVAL, Stage.SA_APPROVAL}
            else "PENDING"
        )

        if target in TERMINALS:
            state.status = target.value

        state.reason = reason

        self.event(
            state,
            "transition",
            source=source,
            target=target,
            reason=reason,
        )
        self.save(state)

    def reset(self):
        """
        Reset only active runtime state.

        Artifacts, approvals and run history remain intact. The next
        `factory analyze` reconstructs the earliest stage that actually needs
        work from the retained approved artifacts and their source digests.
        """
        state = self.load()

        if state:
            self.event(
                state,
                "reset",
                reason=(
                    "Human reset; runtime state cleared. "
                    "Artifacts, approvals and run history retained; "
                    "next analyze reconstructs the earliest required stage."
                ),
            )

        self.path.unlink(missing_ok=True)
