import json
import re
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

from .approvals import ApprovalStore
from .artifacts import Artifact, load_artifact, load_yaml, validate_artifact
from .config import Config, safe_path
from .exceptions import ConcurrencyError, GateError, PipelineError, ValidationError
from .git_utils import architecture_diff, architecture_snapshot, inspect_git, snapshot
from .gates import ba_gate, sa_gate
from .models import PipelineState, Stage
from .state import StateStore, TERMINALS, atomic_write, write_json


BA_PATH = "docs/requirements/business-analysis.yaml"
SA_PATH = "docs/requirements/system-analysis.yaml"


class Pipeline:
    def __init__(self, root, runner):
        self.root = Path(root).resolve()
        self.runner = runner
        self.store = StateStore(self.root)
        self.approvals = ApprovalStore(self.root)
        self.config = Config(self.root)

    def analyze(self):
        with self.store.lock():
            if self.store.load():
                raise PipelineError("Run already exists. Use factory resume or factory reset")
            git_context = inspect_git(self.root)
            if git_context["branch"] in {"main", "master", ""}:
                raise PipelineError("Write stages require a feature branch; preserve dirty changes before selecting one")
            inputs = self.source_snapshot()
            state = PipelineState(run_id=str(uuid4()), pipeline="requirements-to-architecture",
                                  inputs={"sources": inputs}, config_digest=self.config.digest)
            self.store.save(state)
            self.store.event(state, "run_created", git=git_context, business_sources=inputs)
            return self._resume(state)

    def resume(self):
        with self.store.lock():
            state = self.store.load()
            if not state:
                raise PipelineError("No active run. Use factory analyze")
            return self._resume(state)

    def _agent_artifact(self, state, agent, path, ba=None):
        output = safe_path(self.root, path)
        original = output.read_bytes() if output.exists() else None
        before = snapshot(self.root)
        git_context = inspect_git(self.root)
        if git_context["branch"] in {"main", "master", ""}:
            raise PipelineError("Write stage requires a feature branch")
        state.status = "RUNNING"
        self.store.save(state)
        context = {"output": path, "business_input": ba.identity if ba else None,
                   "sources": state.inputs["sources"], "reservation": {"writer": agent, "worktree": str(self.root), "path": path},
                   "approved_ba_evidence": self.approvals.validate(ba) if ba else None}
        self.store.event(state, "agent_start", agent=agent, inputs=context, git=git_context)
        started = time.monotonic()
        result = self.runner.run(agent, f"Follow your existing role contract. Inspect changed business sources. Produce {path}. Stop after your own analysis; never invoke another stage or approve artifacts. Return file proposals only.", context)
        if set(result.files) != {path}:
            raise PipelineError(f"{agent} must propose only {path}")
        raw = result.files[path].encode()
        artifact = validate_artifact(Artifact(output, load_yaml(raw), raw), "system_analysis" if ba else "business_analysis", ba)
        if artifact.data["approval"] is not None or artifact.status == "APPROVED":
            raise PipelineError("Agents cannot issue approval")
        if original is not None:
            previous = load_artifact(output)
            if artifact.revision <= previous.revision or artifact.data["artifact_id"] != previous.data["artifact_id"]:
                raise PipelineError("Changed analysis must preserve artifact ID and increment revision")
        self.assert_snapshot(before)
        self.assert_git_identity(git_context)
        if (output.read_bytes() if output.exists() else None) != original:
            raise ConcurrencyError("Output changed during agent execution; proposal not applied")
        if ba:
            current = ba_gate(self.root / BA_PATH, self.approvals)
            if current.identity != ba.identity:
                raise ConcurrencyError("Approved BA changed during SA execution")
        atomic_write(output, raw)
        self.store.event(state, "agent_finish", agent=agent, output=artifact.identity, duration=time.monotonic() - started)
        # Keep RUNNING persisted until the caller commits the next transition.
        return artifact

    def _resume(self, state):
        if state.stage in TERMINALS:
            if state.stage == Stage.DONE:
                try:
                    self.check_inputs(state)
                    reviewed = self.read_run(state, "reviewed-architecture.json")
                    if architecture_snapshot(snapshot(self.root)) != reviewed:
                        raise GateError("Architecture changed since completed review")
                    state.status = "DONE"
                    state.reason = None
                except PipelineError as error:
                    state.status = "STALE"
                    state.reason = str(error)
                    self.store.event(state, "completed_run_stale", reason=str(error))
                self.store.save(state)
            return state
        if state.status == "RUNNING":
            self.store.transition(state, Stage.HUMAN_REQUIRED, "Interrupted agent execution; inspect outputs/history, then reset deliberately")
            return state
        try:
            if state.config_digest != self.config.digest:
                raise GateError("Pipeline configuration changed during run; inspect and reset")
            if state.inputs["sources"] != self.source_snapshot():
                raise GateError("Business sources changed during run; reset and regenerate analysis")
            while True:
                if state.stage == Stage.BUSINESS_ANALYSIS:
                    artifact = self._agent_artifact(state, self.config.agent("business_analysis"), BA_PATH)
                    if artifact.blockers or artifact.status == "BLOCKED":
                        self.store.transition(state, Stage.BLOCKED, "BA reports unresolved blockers")
                        return state
                    ba_gate(self.root / BA_PATH, self.approvals, False)
                    self.store.transition(state, Stage.BA_APPROVAL)
                    return state
                if state.stage == Stage.BA_APPROVAL:
                    try:
                        ba = ba_gate(self.root / BA_PATH, self.approvals)
                    except GateError as error:
                        state.reason = str(error)
                        self.store.event(state, "gate_failed", reason=str(error))
                        self.store.save(state)
                        return state
                    state.inputs["ba"] = ba.identity
                    self.store.event(state, "gate_passed", gate="ba_gate", artifact=ba.identity)
                    self.store.transition(state, Stage.SYSTEM_ANALYSIS)
                elif state.stage == Stage.SYSTEM_ANALYSIS:
                    ba = ba_gate(self.root / BA_PATH, self.approvals)
                    if state.inputs["ba"] != ba.identity:
                        raise GateError("BA changed after handoff; reset and regenerate")
                    artifact = self._agent_artifact(state, self.config.agent("system_analysis"), SA_PATH, ba)
                    if artifact.blockers or artifact.status == "BLOCKED":
                        self.store.transition(state, Stage.BLOCKED, "SA reports unresolved blockers")
                        return state
                    sa_gate(self.root / SA_PATH, self.root / BA_PATH, self.approvals, False)
                    self.store.transition(state, Stage.SA_APPROVAL)
                    return state
                elif state.stage == Stage.SA_APPROVAL:
                    try:
                        sa = sa_gate(self.root / SA_PATH, self.root / BA_PATH, self.approvals)
                        ba = ba_gate(self.root / BA_PATH, self.approvals)
                        if state.inputs["ba"] != ba.identity:
                            raise GateError("Approved BA changed after SA handoff")
                    except GateError as error:
                        state.reason = str(error)
                        self.store.event(state, "gate_failed", reason=str(error))
                        self.store.save(state)
                        return state
                    state.inputs["sa"] = sa.identity
                    self.store.event(state, "gate_passed", gate="sa_gate", artifact=sa.identity)
                    self.store.transition(state, Stage.ARCHITECTURE)
                elif state.stage in {Stage.ARCHITECTURE, Stage.ARCH_FIX}:
                    self.check_inputs(state)
                    if state.stage == Stage.ARCHITECTURE:
                        baseline = self.capture_baseline(state)
                    else:
                        baseline = self.read_run(state, "architecture-baseline.json")
                    self.run_architect(state, baseline)
                    self.store.transition(state, Stage.ARCHITECTURE_REVIEW)
                elif state.stage == Stage.ARCHITECTURE_REVIEW:
                    self.check_inputs(state)
                    review = self.run_review(state)
                    if review["status"] == "APPROVED":
                        self.store.transition(state, Stage.ARCH_VALIDATION)
                    elif state.attempt >= 3:
                        self.store.transition(state, Stage.HUMAN_REQUIRED, "Three architecture reviews rejected. Inspect exact findings; automatic retries stopped")
                        return state
                    else:
                        state.attempt += 1
                        self.store.transition(state, Stage.ARCH_FIX)
                elif state.stage == Stage.ARCH_VALIDATION:
                    self.check_inputs(state)
                    self.run_validation(state)
                    self.store.transition(state, Stage.DONE)
                    return state
                else:
                    return state
        except (PipelineError, OSError, ValueError, TypeError, KeyError) as error:
            self.store.transition(state, Stage.FAILED, str(error))
            return state

    def source_snapshot(self):
        result = {}
        from .artifacts import digest_bytes
        for relative in self.config.sources:
            path = safe_path(self.root, relative)
            if not path.is_file():
                raise GateError(f"Business source missing: {relative}")
            result[relative] = digest_bytes(path.read_bytes())
        return result

    def assert_snapshot(self, before):
        if snapshot(self.root) != before:
            raise ConcurrencyError("Repository changed during read-only agent/validator execution; no proposal applied. Inspect concurrent writers")

    def assert_git_identity(self, before):
        current = inspect_git(self.root)
        if any(current[key] != before[key] for key in ("head", "branch", "worktrees")):
            raise ConcurrencyError("Git HEAD/branch/worktree changed during stage; proposal not applied")

    def check_inputs(self, state):
        if state.config_digest != Config(self.root).digest:
            raise GateError("Configuration changed; architecture validation baseline is stale")
        ba = ba_gate(self.root / BA_PATH, self.approvals)
        sa = sa_gate(self.root / SA_PATH, self.root / BA_PATH, self.approvals)
        if state.inputs.get("ba") != ba.identity or state.inputs.get("sa") != sa.identity:
            raise GateError("STALE architecture: approved BA/SA identity changed. Reset and regenerate downstream output")
        if state.inputs["sources"] != self.source_snapshot():
            raise GateError("Business sources changed; downstream output is stale")
        return ba, sa

    def read_run(self, state, name):
        return json.loads((self.store.run_dir(state) / name).read_text())

    def capture_baseline(self, state):
        files = architecture_snapshot(snapshot(self.root))
        accepted = [path for path, item in files.items() if "/decisions/" in path and re.search(r"^## Status\s+Accepted\b", item.get("content", ""), re.MULTILINE)]
        baseline = {**inspect_git(self.root), "inputs": state.inputs, "files": files,
                    "accepted_adrs": accepted, "architecture_revision": files.get("docs/architecture/model.json", {}).get("digest")}
        write_json(self.store.run_dir(state) / "architecture-baseline.json", baseline)
        return baseline

    def agent_context(self, state, baseline):
        ba, sa = self.check_inputs(state)
        return {"approved_ba": ba.identity, "approved_sa": sa.identity,
                "ba_approval": self.approvals.validate(ba), "sa_approval": self.approvals.validate(sa),
                "architecture_baseline": baseline, "attempt": state.attempt}

    def run_architect(self, state, baseline):
        before = snapshot(self.root)
        git_context = inspect_git(self.root)
        if git_context["branch"] in {"main", "master", ""}:
            raise PipelineError("Architecture write stage requires a feature branch")
        current = architecture_snapshot(before)
        context = self.agent_context(state, baseline)
        context["reservation"] = {"writer": "architect", "worktree": str(self.root), "scope": "docs/architecture/** excluding validation code and existing Accepted ADRs"}
        context["proposed_diff"] = architecture_diff(baseline["files"], current)
        if state.stage == Stage.ARCH_FIX:
            context["review_findings"] = self.read_run(state, "architecture-review.yaml")
        state.status = "RUNNING"
        self.store.save(state)
        self.store.event(state, "agent_start", agent="architect", inputs=state.inputs, git=git_context)
        started = time.monotonic()
        task = "Inspect existing architecture and approved requirements. Perform impact analysis and update only affected architecture. Preserve valid decisions. Never change existing Accepted ADRs silently; propose a new ADR for new decisions. No application implementation. Return file proposals only. For corrections address the exact review_findings. Include exact consumed BA/SA identities in implementation-handoff.md."
        result = self.runner.run(self.config.agent("arch_fix" if state.stage == Stage.ARCH_FIX else "architecture"), task, context)
        if result.review is not None:
            raise PipelineError("Architect cannot issue review approval")
        proposals = {}
        for relative, content in result.files.items():
            path = safe_path(self.root, relative)
            if not relative.startswith("docs/architecture/") or "/validation/" in relative or path.suffix not in {".md", ".json"}:
                raise PipelineError(f"Architect proposal outside reserved documentation/model scope: {relative}")
            current_accepted = "/decisions/" in relative and re.search(r"^## Status\s+Accepted\b", current.get(relative, {}).get("content", ""), re.MULTILINE)
            if (relative in baseline["accepted_adrs"] or current_accepted) and content != current.get(relative, {}).get("content"):
                raise PipelineError(f"Existing Accepted ADR immutable: {relative}. Create a new ADR")
            if not isinstance(content, str) or not content.strip():
                raise PipelineError("Empty/deletion architecture proposals not supported")
            proposals[path] = content.encode()
        self.assert_snapshot(before)
        self.check_inputs(state)
        self.assert_git_identity(git_context)
        for path, raw in proposals.items():
            atomic_write(path, raw)
        files = architecture_snapshot(snapshot(self.root))
        changed = architecture_diff(baseline["files"], files)
        write_json(self.store.run_dir(state) / "architecture-diff.json", changed)
        self.store.event(state, "agent_finish", agent="architect", changed=[c["path"] for c in changed], duration=time.monotonic() - started)

    def run_review(self, state):
        baseline = self.read_run(state, "architecture-baseline.json")
        before = snapshot(self.root)
        current = architecture_snapshot(before)
        context = self.agent_context(state, baseline)
        context["proposed_diff"] = architecture_diff(baseline["files"], current)
        state.status = "RUNNING"
        self.store.save(state)
        self.store.event(state, "agent_start", agent="architect-reviewer", inputs=state.inputs)
        started = time.monotonic()
        result = self.runner.run(self.config.agent("architecture_review"), "Independently review approved requirements, baseline, exact current architecture diff, ADRs and repository rules. Read-only. Return no files; return review status APPROVED only when all material checks are verified and no blocking findings remain; otherwise REJECTED with concrete findings and expected_action. Do not fix architecture.", context)
        self.assert_snapshot(before)
        self.check_inputs(state)
        review = validate_review(result)
        # JSON is valid YAML and avoids loading generated tags or executing commands.
        write_json(self.store.run_dir(state) / "architecture-review.yaml", review)
        write_json(self.store.run_dir(state) / f"architecture-review-{state.attempt}.yaml", review)
        write_json(self.store.run_dir(state) / "reviewed-architecture.json", current)
        self.store.event(state, "review_result", review_status=review["status"], findings=review["findings"], duration=time.monotonic() - started)
        return review

    def run_validation(self, state):
        reviewed = self.read_run(state, "reviewed-architecture.json")
        before = snapshot(self.root)
        if architecture_snapshot(before) != reviewed:
            raise GateError("Architecture changed after review; cannot validate or mark DONE")
        state.status = "RUNNING"
        self.store.save(state)
        results = []
        for configured in self.config.commands:
            command = [sys.executable, *configured[1:]]
            safe_path(self.root, configured[1])
            started = time.monotonic()
            try:
                process = subprocess.run(command, cwd=self.root, capture_output=True, text=True, timeout=120)
                result = {"command": configured, "returncode": process.returncode,
                          "stdout": process.stdout, "stderr": process.stderr,
                          "duration": time.monotonic() - started}
            except (OSError, subprocess.TimeoutExpired) as error:
                result = {"command": configured, "returncode": -1, "stdout": "", "stderr": str(error)}
            results.append(result)
            write_json(self.store.run_dir(state) / "validation-results.json", results)
            self.store.event(state, "validation_result", **result)
            if result["returncode"]:
                raise ValidationError(f"Validator failed: {configured}\n{result['stdout']}\n{result['stderr']}")
        self.assert_snapshot(before)
        self.check_inputs(state)


def validate_review(result):
    if result.files or not isinstance(result.review, dict):
        raise PipelineError("Reviewer must return findings only, no file proposals")
    review = result.review
    if review.get("status") not in {"APPROVED", "REJECTED"} or not isinstance(review.get("findings"), list):
        raise PipelineError("Malformed review status/findings")
    ids = set()
    for finding in review["findings"]:
        if not isinstance(finding, dict):
            raise PipelineError("Finding must be an object")
        for key in ("id", "severity", "description", "expected_action"):
            if not isinstance(finding.get(key), str) or not finding[key].strip():
                raise PipelineError(f"Review finding missing {key}")
        if finding["id"] in ids or finding["severity"] not in {"BLOCKER", "CRITICAL", "HIGH", "MEDIUM", "LOW"}:
            raise PipelineError("Duplicate finding ID or invalid severity")
        ids.add(finding["id"])
        for key in ("requirements", "files"):
            if not isinstance(finding.get(key), list) or not all(isinstance(v, str) and v for v in finding[key]):
                raise PipelineError(f"Review finding {key} array required")
        if review["status"] == "APPROVED" and finding["severity"] != "LOW":
            raise PipelineError("APPROVED review contains blocking finding")
    if review["status"] == "REJECTED" and not review["findings"]:
        raise PipelineError("REJECTED review must explain required correction or inability to verify")
    return review
