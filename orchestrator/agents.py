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
    def run(self, agent: str, task: str, context: dict | None=None) -> AgentResult:
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
ROLE_FILES = {'business-analyst': 'business-analyst.toml', 'system-analyst': 'system-analyst.toml', 'architect': 'architect.toml', 'architect-reviewer': 'architecture-reviewer.toml'}
REVIEW_SCHEMA = {'type': 'object', 'additionalProperties': False, 'properties': {'status': {'type': 'string', 'enum': ['APPROVED', 'REJECTED']}, 'findings': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False, 'properties': {'id': {'type': 'string'}, 'severity': {'type': 'string', 'enum': ['BLOCKER', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW']}, 'requirements': {'type': 'array', 'items': {'type': 'string'}}, 'files': {'type': 'array', 'items': {'type': 'string'}}, 'description': {'type': 'string'}, 'expected_action': {'type': 'string'}}, 'required': ['id', 'severity', 'requirements', 'files', 'description', 'expected_action']}}}, 'required': ['status', 'findings']}
RESPONSE_SCHEMA = {'type': 'object', 'additionalProperties': False, 'properties': {'files': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False, 'properties': {'path': {'type': 'string'}, 'content': {'type': 'string'}}, 'required': ['path', 'content']}}, 'review': {'anyOf': [REVIEW_SCHEMA, {'type': 'null'}]}}, 'required': ['files', 'review']}

class CodexAgentRunner(AgentRunner):
    """Execute role contracts through isolated, read-only Codex processes.



    Python/controller owns:

    - role selection,

    - repository writes,

    - approvals,

    - process lifecycle.



    Codex owns only analysis and generation of proposed artifacts.

    """

    def __init__(self, root, timeout=1800, progress=None, progress_interval=5):
        self.root = Path(root).resolve()
        self.timeout = timeout
        self.progress = progress
        self.progress_interval = progress_interval

    def _report(self, agent, started, status='running'):
        if self.progress:
            self.progress(agent, time.monotonic() - started, self.timeout, status)

    @staticmethod
    def _terminate_process_group(process):
        """Terminate Codex and all subprocesses started by it."""
        if process.poll() is not None:
            return
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=3)
            return
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
        """
        Execute Codex while continuously draining stdout/stderr.

        Waiting only with process.poll() while stdout/stderr are PIPEs can
        deadlock once Codex fills an OS pipe buffer. communicate() drains both
        pipes while the child is running. After TimeoutExpired it can be called
        again without resending stdin.
        """
        started = time.monotonic()
        try:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=self.root, start_new_session=True)
        except OSError as error:
            raise AgentExecutionError(f'Unable to start Codex for {agent}: {error}') from error
        first_communicate = True
        try:
            self._report(agent, started)
            while True:
                elapsed = time.monotonic() - started
                remaining = self.timeout - elapsed
                if remaining <= 0:
                    self._report(agent, started, 'timeout')
                    self._terminate_process_group(process)
                    try:
                        process.communicate(timeout=3)
                    except subprocess.TimeoutExpired:
                        self._terminate_process_group(process)
                    raise subprocess.TimeoutExpired(command, self.timeout)
                self._report(agent, started)
                slice_timeout = min(self.progress_interval, remaining)
                try:
                    if first_communicate:
                        stdout, stderr = process.communicate(input=prompt, timeout=slice_timeout)
                        first_communicate = False
                    else:
                        stdout, stderr = process.communicate(timeout=slice_timeout)
                    break
                except subprocess.TimeoutExpired:
                    first_communicate = False
                    continue
            status = 'finished' if process.returncode == 0 else 'failed'
            self._report(agent, started, status)
            return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
        except KeyboardInterrupt:
            self._terminate_process_group(process)
            self._report(agent, started, 'interrupted')
            raise
        except subprocess.TimeoutExpired:
            self._terminate_process_group(process)
            raise
        except BaseException:
            self._terminate_process_group(process)
            self._report(agent, started, 'failed')
            raise

    @staticmethod
    def _parse_events(stdout: str) -> list[dict]:
        events = []
        for line_number, line in enumerate(stdout.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f'Invalid Codex JSON event on line {line_number}: {error.msg}') from error
            if not isinstance(event, dict):
                raise ValueError(f'Codex event on line {line_number} is not an object')
            events.append(event)
        if not events:
            raise ValueError('Codex returned no JSON events')
        return events

    @staticmethod
    def _extract_runtime_error(events: list[dict]) -> str | None:
        """Extract a safe diagnostic from structured Codex events."""
        for event in reversed(events):
            event_type = event.get('type')
            if event_type not in {'error', 'turn.failed'}:
                continue
            error = event.get('error')
            if isinstance(error, dict):
                message = error.get('message') or error.get('code') or error.get('type')
                if message:
                    return str(message)[:500]
            if isinstance(error, str):
                return error[:500]
            message = event.get('message')
            if isinstance(message, str):
                return message[:500]
            return event_type
        return None

    @staticmethod
    def _extract_report(events: list[dict]) -> dict:
        messages = []
        for event in events:
            if event.get('type') != 'item.completed':
                continue
            item = event.get('item')
            if not isinstance(item, dict):
                continue
            if item.get('type') != 'agent_message':
                continue
            text = item.get('text')
            if isinstance(text, str) and text.strip():
                messages.append(text)
        if not messages:
            raise ValueError('Codex completed without an agent_message')
        last_error = None
        for message in reversed(messages):
            try:
                report = json.loads(message)
            except json.JSONDecodeError as error:
                last_error = error
                continue
            if isinstance(report, dict):
                return report
        if last_error:
            raise ValueError('No agent_message contained a valid JSON response') from last_error
        raise ValueError('No valid structured Codex response found')

    @staticmethod
    def _validate_report(report: dict):
        if set(report.keys()) != {'files', 'review'}:
            raise ValueError('Codex response must contain exactly files and review')
        files = report['files']
        if not isinstance(files, list):
            raise ValueError('files must be an array')
        paths = set()
        for index, file in enumerate(files):
            if not isinstance(file, dict):
                raise ValueError(f'files[{index}] must be an object')
            if set(file.keys()) != {'path', 'content'}:
                raise ValueError(f'files[{index}] must contain exactly path and content')
            path = file.get('path')
            content = file.get('content')
            if not isinstance(path, str) or not path:
                raise ValueError(f'files[{index}].path must be a non-empty string')
            if not isinstance(content, str):
                raise ValueError(f'files[{index}].content must be a string')
            if path in paths:
                raise ValueError(f'Duplicate proposal path: {path}')
            paths.add(path)
        review = report['review']
        if review is not None and (not isinstance(review, dict)):
            raise ValueError('review must be an object or null')

    @staticmethod
    def _safe_failure_hint(stderr: str) -> str:
        """Classify common Codex failures without persisting raw stderr."""
        text = (stderr or '').lower()
        patterns = [(('rate limit', 'rate_limit', 'too many requests', '429'), 'rate limit exceeded'), (('quota', 'insufficient_quota', 'usage limit', 'credit balance'), 'quota/usage limit exceeded'), (('context length', 'context_length', 'maximum context', 'too many tokens'), 'model context/token limit exceeded'), (('authentication', 'unauthorized', 'invalid api key', '401'), 'authentication failed'), (('forbidden', 'permission denied', '403'), 'permission denied')]
        for needles, description in patterns:
            if any((needle in text for needle in needles)):
                return description
        return 'runtime/provider failure'

    def run(self, agent, task, context=None):
        if agent not in ROLE_FILES:
            raise AgentExecutionError(f'Unknown role: {agent}')
        role_path = self.root / '.codex' / 'agents' / ROLE_FILES[agent]
        try:
            definition = tomllib.loads(role_path.read_text(encoding='utf-8'))
        except (OSError, tomllib.TOMLDecodeError) as error:
            raise AgentExecutionError(f'Unable to load role contract for {agent}: {error}') from error
        if definition.get('name') != agent or not definition.get('developer_instructions'):
            raise AgentExecutionError(f'Role name/instructions mismatch for {agent}')
        protocol = "\n\nOrchestration transport: the controller alone owns repository writes and approvals.\n\n\n\nYou are read-only. Where your role asks you to write an artifact, instead return\n\nits complete proposed UTF-8 content in files[{path,content}].\n\n\n\nNever:\n\n- call factory,\n\n- request write/escalation,\n\n- spawn agents,\n\n- alter controller state,\n\n- issue approvals,\n\n- execute repository writes,\n\n- include shell commands intended for execution by the controller.\n\n\n\nFollow the existing role contract's analysis and verification responsibilities.\n\nReport only your own stage.\n\n\n\nReviewer:\n\n- returns files=[]\n\n- returns a machine-readable review.\n\n\n\nOther roles:\n\n- return review=null.\n\n\n\nInterpret supplied external approval evidence and its exact digest as mandatory\n\nin addition to embedded artifact metadata.\n\n\n\nNo tool may write to the repository.\n\n"
        with tempfile.TemporaryDirectory(prefix='factory-codex-') as temporary:
            schema = Path(temporary) / 'response.schema.json'
            schema.write_text(json.dumps(RESPONSE_SCHEMA, ensure_ascii=False), encoding='utf-8')
            instructions = definition['developer_instructions'] + '\n' + protocol
            command = ['codex', 'exec', '--ignore-user-config', '--ignore-rules', '--strict-config', '--json', '--sandbox', 'read-only', '--cd', str(self.root), '-c', 'approval_policy="never"', '-c', 'agents.enabled=false', '-c', 'developer_instructions=' + json.dumps(instructions, ensure_ascii=False), '--output-schema', str(schema), '-']
            reasoning_effort = definition.get('model_reasoning_effort')
            if reasoning_effort:
                command[2:2] = ['-c', 'model_reasoning_effort=' + json.dumps(reasoning_effort)]
            prompt = task + '\n\nExact controller context:\n' + json.dumps(context or {}, ensure_ascii=False)
            try:
                process = self._execute(command, prompt, agent)
            except subprocess.TimeoutExpired as error:
                raise AgentExecutionError(f'Codex {agent} timed out after {self.timeout:g}s') from error
            except OSError as error:
                raise AgentExecutionError(f'Codex {agent} unavailable: {error}') from error
            events = []
            if process.stdout.strip():
                try:
                    events = self._parse_events(process.stdout)
                except ValueError:
                    if process.returncode == 0:
                        raise
            if process.returncode != 0:
                runtime_error = self._extract_runtime_error(events) if events else None
                hint = self._safe_failure_hint(process.stderr)
                detail = f': {runtime_error}' if runtime_error else ''
                raise AgentExecutionError(f'Codex {agent} exited {process.returncode} ({hint}){detail}')
            try:
                runtime_error = self._extract_runtime_error(events)
                if runtime_error:
                    raise ValueError(f'Runtime reported failure: {runtime_error}')
                report = self._extract_report(events)
                self._validate_report(report)
                files = {file['path']: file['content'] for file in report['files']}
                return AgentResult(files, report['review'])
            except (ValueError, KeyError, TypeError, IndexError) as error:
                raise AgentExecutionError(f'Invalid Codex {agent} output: {error}') from error
