from abc import ABC, abstractmethod
import json
import os
import signal
import subprocess
import tempfile
import time
import tomllib
from pathlib import Path

from .exceptions import AgentExecutionError, PipelineError
from .models import AgentResult
from .patches import check_schema, patch_schema
from .sources import POLICY


class AgentRunner(ABC):
    @abstractmethod
    def run(
        self,
        agent: str,
        task: str,
        context: dict | None = None,
    ) -> AgentResult:
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


def unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


ROLE_FILES = {
    "business-analyst": "business-analyst.toml",
    "system-analyst": "system-analyst.toml",
    "architect": "architect.toml",
    "architect-reviewer": "architecture-reviewer.toml",
}


REVIEW_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "status": {
            "type": "string",
            "enum": ["APPROVED", "REJECTED"],
        },
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "string"},
                    "severity": {
                        "type": "string",
                        "enum": [
                            "BLOCKER",
                            "CRITICAL",
                            "HIGH",
                            "MEDIUM",
                            "LOW",
                        ],
                    },
                    "requirements": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "description": {"type": "string"},
                    "expected_action": {"type": "string"},
                },
                "required": [
                    "id",
                    "severity",
                    "requirements",
                    "files",
                    "description",
                    "expected_action",
                ],
            },
        },
    },
    "required": ["status", "findings"],
}


RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "files": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
        "review": {
            "anyOf": [
                REVIEW_SCHEMA,
                {"type": "null"},
            ],
        },
    },
    "required": ["files", "review"],
}


class CodexAgentRunner(AgentRunner):
    """Execute role contracts through isolated, read-only Codex processes.

    Python/controller owns:
    - role selection,
    - repository writes,
    - approvals,
    - process lifecycle.

    Codex owns only analysis and generation of proposed artifacts.
    """

    def __init__(
        self,
        root,
        timeout=1800,
        progress=None,
        progress_interval=2,
    ):
        self.root = Path(root).resolve()
        self.timeout = timeout
        self.progress = progress
        self.progress_interval = progress_interval

    def _report(self, agent, started, status="running"):
        if self.progress:
            self.progress(
                agent,
                time.monotonic() - started,
                self.timeout,
                status,
            )

    @staticmethod
    def _terminate_process_group(process):
        """Terminate Codex and all subprocesses started by it."""

        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return

        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            pass

        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            pass

    def _execute(self, command, prompt, agent):
        started = time.monotonic()

        try:
            process = subprocess.Popen(
                command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, cwd=self.root, start_new_session=True,
            )
        except OSError as error:
            raise AgentExecutionError("CODEX_START_FAILED") from error
        try:
            pending_input = prompt
            while True:
                elapsed = time.monotonic() - started
                if elapsed >= self.timeout:
                    self._report(agent, started, "timeout")
                    raise subprocess.TimeoutExpired(command, self.timeout)
                self._report(agent, started)
                try:
                    stdout, stderr = process.communicate(
                        input=pending_input,
                        timeout=min(self.progress_interval, max(.001, self.timeout - elapsed)),
                    )
                    self._report(agent, started, "finished" if process.returncode == 0 else "failed")
                    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
                except subprocess.TimeoutExpired:
                    pending_input = None
        except KeyboardInterrupt:
            self._terminate_process_group(process)
            self._report(agent, started, "interrupted")
            raise
        except subprocess.TimeoutExpired:
            self._terminate_process_group(process)
            raise
        except BaseException:
            self._terminate_process_group(process)
            self._report(agent, started, "failed")
            raise
        finally:
            # Clean descendants even after normal exits with closed inherited pipes.
            self._terminate_process_group(process)
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None:
                    stream.close()

    @staticmethod
    def _parse_events(stdout: str) -> list[dict]:
        events = []

        for line_number, line in enumerate(stdout.splitlines(), start=1):
            line = line.strip()

            if not line:
                continue

            try:
                event = json.loads(line, object_pairs_hook=unique_json_object)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid Codex JSON event on line {line_number}: "
                    f"{error.msg}"
                ) from error

            if not isinstance(event, dict):
                raise ValueError(
                    f"Codex event on line {line_number} is not an object"
                )

            events.append(event)

        if not events:
            raise ValueError("Codex returned no JSON events")

        return events

    @staticmethod
    def _extract_runtime_error(events: list[dict]) -> str | None:
        # Provider messages may contain secrets. Persist only fixed event types.
        return next((event["type"] for event in events
                     if event.get("type") in {"error", "turn.failed"}), None)

    @staticmethod
    def _extract_report(events: list[dict]) -> dict:
        messages = []

        for event in events:
            if event.get("type") != "item.completed":
                continue

            item = event.get("item")

            if not isinstance(item, dict):
                continue

            if item.get("type") != "agent_message":
                continue

            text = item.get("text")

            if isinstance(text, str) and text.strip():
                messages.append(text)

        if not messages:
            raise ValueError(
                "Codex completed without an agent_message"
            )

        # Search backwards because the final agent message should contain
        # the schema-constrained response, but tolerate earlier textual
        # agent messages.
        last_error = None

        for message in reversed(messages):
            try:
                report = json.loads(message, object_pairs_hook=unique_json_object)
            except json.JSONDecodeError as error:
                last_error = error
                continue

            if isinstance(report, dict):
                return report

        if last_error:
            raise ValueError(
                "No agent_message contained a valid JSON response"
            ) from last_error

        raise ValueError(
            "No valid structured Codex response found"
        )

    @staticmethod
    def _validate_report(report: dict):
        if set(report.keys()) != {"files", "review"}:
            raise ValueError(
                "Codex response must contain exactly files and review"
            )

        files = report["files"]

        if not isinstance(files, list):
            raise ValueError("files must be an array")

        paths = set()

        for index, file in enumerate(files):
            if not isinstance(file, dict):
                raise ValueError(
                    f"files[{index}] must be an object"
                )

            if set(file.keys()) != {"path", "content"}:
                raise ValueError(
                    f"files[{index}] must contain exactly path and content"
                )

            path = file.get("path")
            content = file.get("content")

            if not isinstance(path, str) or not path:
                raise ValueError(
                    f"files[{index}].path must be a non-empty string"
                )

            if not isinstance(content, str):
                raise ValueError(
                    f"files[{index}].content must be a string"
                )

            if path in paths:
                raise ValueError(
                    "Duplicate proposal path"
                )

            paths.add(path)

        review = report["review"]

        if review is not None and not isinstance(review, dict):
            raise ValueError(
                "review must be an object or null"
            )

    @staticmethod
    def _safe_failure_hint(stderr: str) -> str:
        """Classify common Codex failures without persisting raw stderr."""

        text = (stderr or "").lower()

        patterns = [
            (
                (
                    "rate limit",
                    "rate_limit",
                    "too many requests",
                    "429",
                ),
                "rate limit exceeded",
            ),
            (
                (
                    "quota",
                    "insufficient_quota",
                    "usage limit",
                    "credit balance",
                ),
                "quota/usage limit exceeded",
            ),
            (
                (
                    "context length",
                    "context_length",
                    "maximum context",
                    "too many tokens",
                ),
                "model context/token limit exceeded",
            ),
            (
                (
                    "authentication",
                    "unauthorized",
                    "invalid api key",
                    "401",
                ),
                "authentication failed",
            ),
            (
                (
                    "forbidden",
                    "permission denied",
                    "403",
                ),
                "permission denied",
            ),
        ]

        for needles, description in patterns:
            if any(needle in text for needle in needles):
                return description

        return "runtime/provider failure"

    def run(self, agent, task, context=None):
        if agent not in ROLE_FILES:
            raise AgentExecutionError(
                f"Unknown role: {agent}"
            )

        role_path = (
            self.root
            / ".codex"
            / "agents"
            / ROLE_FILES[agent]
        )

        try:
            definition = tomllib.loads(
                role_path.read_text(encoding="utf-8")
            )
        except (OSError, tomllib.TOMLDecodeError) as error:
            raise AgentExecutionError(
                f"Unable to load role contract for {agent}: {error}"
            ) from error

        if (
            definition.get("name") != agent
            or not definition.get("developer_instructions")
        ):
            raise AgentExecutionError(
                f"Role name/instructions mismatch for {agent}"
            )

        protocol = """
Orchestration transport: the controller alone owns repository writes and approvals.

You are read-only. Where your role asks you to write an artifact, instead return
its complete proposed UTF-8 content in files[{path,content}].

Never:
- call factory,
- request write/escalation,
- spawn agents,
- alter controller state,
- issue approvals,
- execute repository writes,
- include shell commands intended for execution by the controller.

Follow the existing role contract's analysis and verification responsibilities.
Report only your own stage.

Reviewer:
- returns files=[]
- returns a machine-readable review.

Other roles:
- return review=null.

Interpret supplied external approval evidence and its exact digest as mandatory
in addition to embedded artifact metadata.

No tool may write to the repository.
"""

        if agent in {"business-analyst", "system-analyst"}:
            protocol += "\nAnalysis source policy:\n" + POLICY
        incremental = agent in {"business-analyst", "system-analyst"} and (context or {}).get("mode") == "INCREMENTAL"
        output_schema = patch_schema("business_analysis" if agent == "business-analyst" else "system_analysis") if incremental else RESPONSE_SCHEMA
        if incremental:
            protocol += "\nINCREMENTAL overrides full-file transport and role write instructions: return ONLY the strict JSON patch object, no files, review, YAML or control metadata. Apply impact only using supplied baseline, delta and open questions. Do not load unchanged business sources or history.\n"

        with tempfile.TemporaryDirectory(
            prefix="factory-codex-"
        ) as temporary:
            schema = Path(temporary) / "response.schema.json"

            schema.write_text(
                json.dumps(
                    output_schema,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            instructions = (
                definition["developer_instructions"]
                + "\n"
                + protocol
            )

            command = [
                "codex",
                "exec",
                "--ignore-user-config",
                "--ignore-rules",
                "--strict-config",
                "--json",
                "--sandbox",
                "read-only",
                "--cd",
                str(self.root),
                "-c",
                'approval_policy="never"',
                "-c",
                "agents.enabled=false",
                "-c",
                "developer_instructions="
                + json.dumps(
                    instructions,
                    ensure_ascii=False,
                ),
                "--output-schema",
                str(schema),
                "-",
            ]

            reasoning_effort = definition.get(
                "model_reasoning_effort"
            )

            if reasoning_effort:
                # Insert config immediately after `exec`.
                command[2:2] = [
                    "-c",
                    "model_reasoning_effort="
                    + json.dumps(reasoning_effort),
                ]

            prompt = (
                task
                + "\n\nExact controller context:\n"
                + json.dumps(
                    context or {},
                    ensure_ascii=False,
                )
            )

            try:
                process = self._execute(
                    command,
                    prompt,
                    agent,
                )

            except subprocess.TimeoutExpired as error:
                raise AgentExecutionError(
                    "CODEX_TIMEOUT"
                ) from error

            except OSError as error:
                raise AgentExecutionError(
                    "CODEX_START_FAILED"
                ) from error

            # Parse structured events even when Codex exits non-zero.
            # They often contain a useful structured failure reason.
            events = []

            if process.stdout.strip():
                try:
                    events = self._parse_events(
                        process.stdout
                    )
                except ValueError:
                    # Exit-code handling below still gives us a useful
                    # classification based on stderr.
                    if process.returncode == 0:
                        raise AgentExecutionError("CODEX_INVALID_OUTPUT: JSON events") from None

            if process.returncode != 0:
                hint = self._safe_failure_hint(process.stderr)
                raise AgentExecutionError(f"CODEX_EXIT_FAILED: {hint}")

            try:
                runtime_error = self._extract_runtime_error(
                    events
                )

                if runtime_error:
                    raise ValueError(
                        f"Runtime reported failure: "
                        f"{runtime_error}"
                    )

                report = self._extract_report(events)

                if incremental:
                    check_schema(report, output_schema)
                    return AgentResult(patch=report)
                self._validate_report(report)

                files = {
                    file["path"]: file["content"]
                    for file in report["files"]
                }

                return AgentResult(
                    files,
                    report["review"],
                )

            except (
                ValueError,
                KeyError,
                TypeError,
                IndexError,
                PipelineError,
            ) as error:
                raise AgentExecutionError(
                    "CODEX_INVALID_OUTPUT: " + ("Duplicate proposals" if "Duplicate proposal" in str(error) else "response validation failed")
                ) from error
