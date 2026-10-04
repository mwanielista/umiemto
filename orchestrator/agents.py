from abc import ABC, abstractmethod
import json
import os
import signal
import subprocess
import tempfile
import time
import tomllib
from pathlib import Path

from .exceptions import AgentExecutionError
from .models import AgentResult


class AgentRunner(ABC):
    @abstractmethod
    def run(self, agent: str, task: str, context: dict | None = None) -> AgentResult:
        """Return proposals. Never change controller state or approve artifacts."""


class FakeAgentRunner(AgentRunner):
    def __init__(self, results):
        self.results = results
        self.calls = []

    def run(self, agent, task, context=None):
        self.calls.append((agent, task, context))
        result = self.results[agent]
        if isinstance(result, list):
            result = result.pop(0)
        if callable(result):
            result = result(context)
        return result


ROLE_FILES = {"business-analyst": "business-analyst.toml", "system-analyst": "system-analyst.toml",
              "architect": "architect.toml", "architect-reviewer": "architecture-reviewer.toml"}

REVIEW_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "status": {"type": "string", "enum": ["APPROVED", "REJECTED"]},
        "findings": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {"id": {"type": "string"}, "severity": {"type": "string", "enum": ["BLOCKER", "CRITICAL", "HIGH", "MEDIUM", "LOW"]},
                           "requirements": {"type": "array", "items": {"type": "string"}},
                           "files": {"type": "array", "items": {"type": "string"}},
                           "description": {"type": "string"}, "expected_action": {"type": "string"}},
            "required": ["id", "severity", "requirements", "files", "description", "expected_action"]}},
    }, "required": ["status", "findings"],
}
RESPONSE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "files": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"]}},
        "review": {"anyOf": [REVIEW_SCHEMA, {"type": "null"}]},
    }, "required": ["files", "review"],
}


class CodexAgentRunner(AgentRunner):
    """Load existing role contracts into separate read-only Codex executions.

    No custom-agent selector or LLM coordinator is needed: Python selects roles.
    User configuration/MCP and delegation are disabled; CLI authentication remains.
    """
    def __init__(self, root, timeout=900, progress=None, progress_interval=2):
        self.root = Path(root).resolve()
        self.timeout = timeout
        self.progress = progress
        self.progress_interval = progress_interval

    def _execute(self, command, prompt, agent):
        started = time.monotonic()
        def report(status="running"):
            if self.progress:
                self.progress(agent, time.monotonic() - started, self.timeout, status)

        # Separate process group lets Ctrl+C/timeout stop Codex and its subprocesses.
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, cwd=self.root,
                                   start_new_session=True)
        try:
            report()
            first = True
            while True:
                remaining = self.timeout - (time.monotonic() - started)
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(command, self.timeout)
                try:
                    stdout, stderr = process.communicate(input=prompt if first else None,
                                                         timeout=min(self.progress_interval, remaining))
                    report("finished" if process.returncode == 0 else "failed")
                    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
                except subprocess.TimeoutExpired:
                    first = False
                    if time.monotonic() - started >= self.timeout:
                        raise
                    report()
        except BaseException as error:
            # Never leave a paid inference or shell child running after cancellation.
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.communicate()
            report("interrupted" if isinstance(error, KeyboardInterrupt) else "timeout" if isinstance(error, subprocess.TimeoutExpired) else "failed")
            raise

    def run(self, agent, task, context=None):
        if agent not in ROLE_FILES:
            raise AgentExecutionError(f"Unknown role: {agent}")
        definition = tomllib.loads((self.root / ".codex/agents" / ROLE_FILES[agent]).read_text())
        if definition.get("name") != agent or not definition.get("developer_instructions"):
            raise AgentExecutionError("Role name/instructions mismatch")
        protocol = """
Orchestration transport: the controller alone owns repository writes and approvals.
You are read-only; where your role asks you to write an artifact, instead return
its complete proposed UTF-8 content in files[{path,content}]. Never call factory,
request write/escalation, spawn agents, alter state or issue approvals. Never
include shell commands for execution by the controller. Follow the existing role
contract's analysis and verification responsibilities; report only your stage.
Reviewer returns files=[] and machine-readable review. Other roles return
review=null. Interpret the supplied external approval evidence and exact digest
as mandatory in addition to embedded metadata. No tool may write to the repo.
"""
        with tempfile.TemporaryDirectory(prefix="factory-codex-") as temporary:
            schema = Path(temporary) / "response.schema.json"
            schema.write_text(json.dumps(RESPONSE_SCHEMA))
            instructions = definition["developer_instructions"] + "\n" + protocol
            command = ["codex", "exec", "--ignore-user-config", "--ignore-rules", "--strict-config",
                       "--json", "--sandbox", "read-only", "--cd", str(self.root),
                       "-c", "approval_policy=\"never\"", "-c", "agents.enabled=false",
                       "-c", "developer_instructions=" + json.dumps(instructions),
                       "--output-schema", str(schema), "-"]
            if definition.get("model_reasoning_effort"):
                command[2:2] = ["-c", "model_reasoning_effort=" + json.dumps(definition["model_reasoning_effort"])]
            prompt = task + "\nExact controller context:\n" + json.dumps(context or {}, ensure_ascii=False)
            try:
                process = self._execute(command, prompt, agent)
            except (OSError, subprocess.TimeoutExpired) as error:
                raise AgentExecutionError(f"Codex {agent} unavailable or timed out; inspect local Codex authentication/sandbox") from error
            if process.returncode:
                # Do not persist arbitrary stderr: provider output can contain credentials.
                raise AgentExecutionError(f"Codex {agent} exited {process.returncode}; inspect local runtime configuration (raw provider output not logged)")
            try:
                events = [json.loads(line) for line in process.stdout.splitlines() if line.strip()]
                if any(e.get("type") in {"error", "turn.failed"} for e in events):
                    raise ValueError("Runtime reported failure")
                messages = [e["item"]["text"] for e in events if e.get("type") == "item.completed"
                            and e.get("item", {}).get("type") == "agent_message"]
                report = json.loads(messages[-1])
                files = report["files"]
                if not isinstance(files, list) or any(not isinstance(f, dict) or not isinstance(f.get("path"), str) or not isinstance(f.get("content"), str) for f in files):
                    raise ValueError("Malformed proposal files")
                if len({f["path"] for f in files}) != len(files):
                    raise ValueError("Duplicate proposal paths")
                return AgentResult({f["path"]: f["content"] for f in files}, report["review"])
            except (ValueError, KeyError, TypeError, IndexError) as error:
                raise AgentExecutionError(f"Invalid Codex {agent} output: {error}") from error
