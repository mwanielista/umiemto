import copy
import tempfile
import unittest
import shutil
import subprocess
from pathlib import Path

import yaml

from orchestrator.agents import FakeAgentRunner
from orchestrator.approvals import ApprovalStore
from orchestrator.artifacts import BA_SECTIONS, SA_SECTIONS, load_artifact
from orchestrator.exceptions import GateError, PipelineError
from orchestrator.gates import ba_gate, sa_gate
from orchestrator.models import AgentResult, PipelineState, Stage
from orchestrator.pipeline import BA_PATH, SA_PATH, Pipeline, validate_review
from orchestrator.state import StateStore
from orchestrator.cli import approve, status
from orchestrator.config import Config
from orchestrator.exceptions import ConcurrencyError


def fixture(kind="business_analysis", ba=None):
    sections = BA_SECTIONS if ba is None else SA_SECTIONS
    d = {"schema_version": 1, "artifact_type": kind, "artifact_id": "BA" if ba is None else "SA",
         "revision": 1, "status": "READY_FOR_REVIEW", "scope": "Test scope; excludes unrelated work",
         "sources": [{"id": "SRC-001", "location": "AGENTS.md", "revision": "test-commit"}],
         "approval": None, "assumptions": [], "constraints": [], "open_questions": [],
         "section_notes": {s: "Not applicable in focused test scope" for s in (*sections, "assumptions", "constraints", "open_questions")}}
    d.update({s: [] for s in sections})
    req = {"id": "BR-001", "description": "A requirement", "rationale": "A reason", "priority": "MUST",
           "acceptance_criteria": ["Observable result"], "source_refs": [{"source_id": "SRC-001", "locator": "section 1"}]}
    if ba is None:
        d["business_requirements"] = [req]
    else:
        d["business_input"] = ba.identity
        d["functional_requirements"] = [{**req, "id": "FR-001", "br_refs": ["BR-001"]}]
        d["non_functional_requirements"] = [{**req, "id": "NFR-001", "br_refs": ["BR-001"]}]
        d["br_coverage"] = [{"br_id": "BR-001", "requirement_refs": ["FR-001", "NFR-001"], "exclusion_reason": None}]
    return d


class FactoryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.approvals = ApprovalStore(self.root)
        repository = Path(__file__).resolve().parents[1]
        shutil.copytree(repository / "config", self.root / "config")
        shutil.copytree(repository / "orchestrator", self.root / "orchestrator", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(repository / "docs/business", self.root / "docs/business")
        shutil.copytree(repository / ".codex/agents", self.root / ".codex/agents")
        shutil.copytree(repository / "docs/architecture", self.root / "docs/architecture")
        shutil.copytree(repository / "docs/requirements", self.root / "docs/requirements")
        for relative in ("AGENTS.md", "workflow.md", "docs/orchestrator.md", "docs/biznesplan-platforma-kursy-dla-dzieci.md", "docs/szablon-programu-edukacyjnego-modul-4-zajecia.md"):
            shutil.copyfile(repository / relative, self.root / relative)
        # Bootstrap tests require absence; legacy adoption has its own tests.
        (self.root / BA_PATH).unlink(missing_ok=True)
        subprocess.run(["git", "init", "-b", "feature/test", str(self.root)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--allow-empty", "-m", "Test baseline"], check=True, capture_output=True)

    def write(self, path, d):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(yaml.safe_dump(d, sort_keys=False))
        return load_artifact(p)

    def approve(self, artifact, ba=None):
        self.approvals.commit(artifact, self.approvals.candidate(artifact, "TEST_OWNER", ba))
        return load_artifact(artifact.path)

    def test_vertical_slice_waits_then_passes_exact_ba_to_fake_sa(self):
        runner = FakeAgentRunner({"business-analyst": AgentResult({BA_PATH: yaml.safe_dump(fixture())}),
                                  "system-analyst": lambda context: AgentResult({SA_PATH: yaml.safe_dump(fixture("system_analysis", load_artifact(self.root / BA_PATH)))})})
        p = Pipeline(self.root, runner)
        self.assertEqual(p.analyze().stage, Stage.BA_APPROVAL)
        self.assertEqual(p.resume().stage, Stage.BA_APPROVAL)
        self.assertEqual(len(runner.calls), 1)
        ba = self.approve(load_artifact(self.root / BA_PATH))
        # New controller proves persistence across process lifetimes.
        self.assertEqual(Pipeline(self.root, runner).resume().stage, Stage.SA_APPROVAL)
        self.assertEqual(runner.calls[-1][2]["business_input"], ba.identity)
        p.resume()
        self.assertEqual(len(runner.calls), 2)

    def test_ba_gate_negative_cases_and_valid_approval(self):
        with self.assertRaises(GateError):
            ba_gate(self.root / BA_PATH, self.approvals)
        a = self.write(BA_PATH, fixture())
        with self.assertRaisesRegex(GateError, "MISSING approval"):
            ba_gate(a.path, self.approvals)
        a = self.approve(a)
        self.assertEqual(ba_gate(a.path, self.approvals).digest, a.digest)
        for change in (lambda d: d.update(revision=2), lambda d: d.update(scope="Changed content"),
                       lambda d: d["business_requirements"].append(copy.deepcopy(d["business_requirements"][0])),
                       lambda d: d["business_requirements"][0].update(acceptance_criteria=[]),
                       lambda d: d["business_requirements"][0].update(source_refs=[])):
            with self.subTest(change=change):
                d = copy.deepcopy(a.data)
                change(d)
                candidate = self.write(BA_PATH, d)
                with self.assertRaises(GateError):
                    ba_gate(candidate.path, self.approvals)
        a.path.write_text("key: [unterminated")
        with self.assertRaises(GateError):
            ba_gate(a.path, self.approvals)

    def test_blocked_analysis(self):
        d = fixture()
        d["status"] = "BLOCKED"
        d["open_questions"] = [{"id": "Q-001", "question": "Missing decision", "severity": "BLOCKER", "owner": "owner", "affected_refs": ["BR-001"], "status": "OPEN", "resolution": None}]
        a = self.write(BA_PATH, d)
        with self.assertRaisesRegex(GateError, "BLOCKED"):
            ba_gate(a.path, self.approvals)
        p = Pipeline(self.root, FakeAgentRunner({"business-analyst": AgentResult({BA_PATH: yaml.safe_dump(d)})}))
        (self.root / BA_PATH).unlink()
        self.assertEqual(p.analyze().stage, Stage.BLOCKED)
        self.assertTrue(p.resume().reason)

    def test_state_transitions_fail_closed(self):
        store = StateStore(self.root)
        s = PipelineState("test", "pipeline")
        with self.assertRaises(PipelineError):
            store.transition(s, Stage.DONE)
        store.transition(s, Stage.BA_APPROVAL)
        self.assertEqual(store.load().stage, Stage.BA_APPROVAL)
        with self.assertRaises(PipelineError):
            store.transition(s, Stage.FAILED)
        store.transition(s, Stage.FAILED, "Reason")
        self.assertEqual(store.load().reason, "Reason")

    def test_sa_gate_rejects_stale_inputs_traceability_blockers_and_missing_approval(self):
        ba = self.approve(self.write(BA_PATH, fixture()))
        with self.assertRaises(GateError):
            sa_gate(self.root / SA_PATH, ba.path, self.approvals)
        original = fixture("system_analysis", ba)
        for mutation in (lambda d: d["business_input"].update(revision=9),
                         lambda d: d["business_input"].update(content_digest="sha256:wrong"),
                         lambda d: d["functional_requirements"][0].update(br_refs=["BR-999"]),
                         lambda d: d["non_functional_requirements"][0].update(br_refs=[]),
                         lambda d: d["non_functional_requirements"][0].update(acceptance_criteria=[]),
                         lambda d: d.update(br_coverage=[])):
            with self.subTest(mutation=mutation):
                d = copy.deepcopy(original)
                mutation(d)
                a = self.write(SA_PATH, d)
                with self.assertRaises(GateError):
                    sa_gate(a.path, ba.path, self.approvals, False)
        d = copy.deepcopy(original)
        d["status"] = "BLOCKED"
        d["open_questions"] = [{"id": "Q-001", "question": "Unknown", "owner": "owner", "severity": "BLOCKER", "affected_refs": ["FR-001"], "status": "OPEN", "resolution": None}]
        a = self.write(SA_PATH, d)
        with self.assertRaisesRegex(GateError, "BLOCKED"):
            sa_gate(a.path, ba.path, self.approvals, False)
        a = self.write(SA_PATH, original)
        with self.assertRaisesRegex(GateError, "MISSING"):
            sa_gate(a.path, ba.path, self.approvals)
        a = self.approve(a, ba)
        self.assertEqual(sa_gate(a.path, ba.path, self.approvals).digest, a.digest)
        (self.root / BA_PATH).write_bytes(ba.raw + b"\n")
        with self.assertRaises(GateError):
            sa_gate(a.path, ba.path, self.approvals)

    def run_to_sa_approval(self, reviews):
        runner = FakeAgentRunner({"business-analyst": AgentResult({BA_PATH: yaml.safe_dump(fixture())}),
                                  "system-analyst": lambda c: AgentResult({SA_PATH: yaml.safe_dump(fixture("system_analysis", load_artifact(self.root / BA_PATH)))}),
                                  "architect": AgentResult({"docs/architecture/orchestration-test.md": "# Architecture test\nFocused test architecture\n"}),
                                  "architect-reviewer": reviews})
        p = Pipeline(self.root, runner)
        self.assertEqual(p.analyze().stage, Stage.BA_APPROVAL)
        ba = self.approve(load_artifact(self.root / BA_PATH))
        self.assertEqual(p.resume().stage, Stage.SA_APPROVAL)
        self.approve(load_artifact(self.root / SA_PATH), ba)
        return p, runner

    def test_end_to_end_approved_review_and_executable_validation(self):
        p, runner = self.run_to_sa_approval(AgentResult(review={"status": "APPROVED", "findings": []}))
        self.assertEqual(p.resume().stage, Stage.DONE)
        count = len(runner.calls)
        self.assertEqual(p.resume().stage, Stage.DONE)
        self.assertEqual(len(runner.calls), count)
        directory = p.store.run_dir(p.store.load())
        self.assertTrue((directory / "architecture-baseline.json").exists())
        self.assertIn("PASS", status(p))
        (self.root / "docs/architecture/orchestration-test.md").write_text("Changed after review")
        self.assertIn("PIPELINE: STALE", status(p))

    @staticmethod
    def rejected():
        return AgentResult(review={"status": "REJECTED", "findings": [{"id": "ARCH-REV-001", "severity": "HIGH", "requirements": ["FR-001"], "files": ["docs/architecture/orchestration-test.md"], "description": "Missing semantics", "expected_action": "Define semantics"}]})

    def test_review_retry_exact_findings_then_approved(self):
        p, runner = self.run_to_sa_approval([self.rejected(), AgentResult(review={"status": "APPROVED", "findings": []})])
        s = p.resume()
        self.assertEqual(s.stage, Stage.DONE)
        self.assertEqual(s.attempt, 2)
        fixes = [c for c in runner.calls if c[0] == "architect"]
        self.assertEqual(fixes[-1][2]["review_findings"], self.rejected().review)

    def test_third_rejection_requires_human(self):
        p, runner = self.run_to_sa_approval([self.rejected(), self.rejected(), self.rejected()])
        s = p.resume()
        self.assertEqual(s.stage, Stage.HUMAN_REQUIRED)
        self.assertEqual(s.attempt, 3)
        self.assertEqual(sum(c[0] == "architect-reviewer" for c in runner.calls), 3)
        self.assertFalse((p.store.run_dir(s) / "validation-results.json").exists())

    def test_validator_failure_never_done(self):
        p, runner = self.run_to_sa_approval(AgentResult(review={"status": "APPROVED", "findings": []}))
        runner.results["architect"] = AgentResult({"docs/architecture/model.json": "{}"})
        s = p.resume()
        self.assertEqual(s.stage, Stage.FAILED)
        self.assertIn("Validator failed", s.reason)

    def test_dirty_baseline_preserves_preexisting_changes(self):
        path = self.root / "docs/architecture/preexisting.md"
        path.write_text("# Existing dirty content\n")
        p, _ = self.run_to_sa_approval(AgentResult(review={"status": "APPROVED", "findings": []}))
        s = p.resume()
        self.assertEqual(s.stage, Stage.DONE)
        baseline = p.read_run(s, "architecture-baseline.json")
        diff = p.read_run(s, "architecture-diff.json")
        self.assertIn("docs/architecture/preexisting.md", baseline["files"])
        self.assertNotIn("docs/architecture/preexisting.md", [c["path"] for c in diff])
        self.assertEqual(path.read_text(), "# Existing dirty content\n")

    def test_architect_cannot_modify_accepted_adrs_or_runtime(self):
        for relative in ("docs/architecture/decisions/0001-modular-monolith-boundaries.md",
                         "docs/architecture/decisions/./0001-modular-monolith-boundaries.md",
                         "docs/architecture/decisions//0001-modular-monolith-boundaries.md",
                         ".orchestrator/approvals/forged.yaml"):
            with self.subTest(path=relative):
                p, runner = self.run_to_sa_approval(AgentResult(review={"status": "APPROVED", "findings": []}))
                runner.results["architect"] = AgentResult({relative: "forged content"})
                self.assertEqual(p.resume().stage, Stage.FAILED)
                with p.store.lock():
                    p.store.reset()
                # fresh test artifacts/approvals next iteration
                for path in (self.root / BA_PATH, self.root / SA_PATH):
                    path.unlink()
                for path in self.approvals.directory.glob("*.yaml"):
                    path.unlink()

    def test_approval_confirmation_cancel_change_and_safe_reset(self):
        runner = FakeAgentRunner({"business-analyst": AgentResult({BA_PATH: yaml.safe_dump(fixture())})})
        p = Pipeline(self.root, runner)
        p.analyze()
        a = load_artifact(self.root / BA_PATH)
        approve(p, "ba", "OWNER", confirm=lambda _: "n", output=lambda _: None)
        self.assertEqual(load_artifact(a.path).digest, a.digest)
        def concurrent(_):
            a.path.write_bytes(a.raw + b"\n")
            return "y"
        with self.assertRaises(ConcurrencyError):
            approve(p, "ba", "OWNER", confirm=concurrent, output=lambda _: None)
        with self.assertRaises(GateError):
            approve(p, "ba", "OWNER", confirm=lambda _: "y", output=lambda _: None)
        # Deliberately restore the exact pinned candidate after the concurrent edit.
        a.path.write_bytes(a.raw)
        approve(p, "ba", "OWNER", confirm=lambda _: "y", output=lambda _: None)
        self.assertTrue(self.approvals.path(load_artifact(a.path)).exists())
        with p.store.lock():
            p.store.reset()
        self.assertIsNone(p.store.load())
        self.assertTrue(a.path.exists())
        self.assertTrue(self.approvals.path(load_artifact(a.path)).exists())

    def test_lock_blocks_second_controller(self):
        first = StateStore(self.root)
        second = StateStore(self.root)
        with first.lock():
            with self.assertRaises(ConcurrencyError):
                with second.lock():
                    self.fail("Lock should not be acquired")

    def test_interrupted_execution_does_not_repeat_agent(self):
        p = Pipeline(self.root, FakeAgentRunner({}))
        s = PipelineState("interrupted", "requirements-to-architecture", status="RUNNING")
        p.store.save(s)
        self.assertEqual(p.resume().stage, Stage.HUMAN_REQUIRED)
        self.assertEqual(p.runner.calls, [])

    def test_configuration_cannot_skip_gates_or_run_shell(self):
        path = self.root / "config/pipeline.yaml"
        original = yaml.safe_load(path.read_text())
        for mutate in (lambda d: d["stages"]["business_analysis"].update(next="architecture"),
                       lambda d: d["stages"]["architecture_validation"].update(commands=[["sh", "-c", "echo bad"]]),
                       lambda d: d["stages"]["architecture_review"].update(retry={"stage": "arch_fix", "max_attempts": 99})):
            d = copy.deepcopy(original)
            mutate(d)
            path.write_text(yaml.safe_dump(d))
            with self.assertRaises(PipelineError):
                Config(self.root)

    def test_review_malformed_or_false_approval_rejected(self):
        for result in (AgentResult(review={"status": "OK", "findings": []}),
                       AgentResult(files={"file": "change"}, review={"status": "APPROVED", "findings": []}),
                       AgentResult(review={"status": "REJECTED", "findings": []}),
                       AgentResult(review={"status": "APPROVED", "findings": self.rejected().review["findings"]})):
            with self.assertRaises(PipelineError):
                validate_review(result)

    def test_concurrent_modification_stops_promotion(self):
        def bad_agent(_):
            (self.root / "docs/architecture/new-concurrent.md").write_text("Unexpected external edit")
            return AgentResult({BA_PATH: yaml.safe_dump(fixture())})
        p = Pipeline(self.root, FakeAgentRunner({"business-analyst": bad_agent}))
        s = p.analyze()
        self.assertEqual(s.stage, Stage.FAILED)
        self.assertIn("Repository changed", s.reason)
        self.assertFalse((self.root / BA_PATH).exists())

    def test_malformed_types_and_duplicate_yaml_fail_as_gate_errors(self):
        for mutate in (lambda d: d.update(status=[]),
                       lambda d: d["business_requirements"][0].update(priority={}),
                       lambda d: d["sources"][0].update(id=[])):
            d = fixture()
            mutate(d)
            a = self.write(BA_PATH, d)
            with self.assertRaises(GateError):
                ba_gate(a.path, self.approvals)
        (self.root / BA_PATH).write_text("revision: 1\nrevision: 2\n")
        with self.assertRaisesRegex(GateError, "Duplicate"):
            ba_gate(self.root / BA_PATH, self.approvals)

    def test_external_evidence_wrong_revision_or_digest_rejected(self):
        a = self.approve(self.write(BA_PATH, fixture()))
        path = self.approvals.path(a)
        original = yaml.safe_load(path.read_text())
        for key, value in (("revision", 99), ("digest", "sha256:wrong")):
            record = copy.deepcopy(original)
            record["artifact"][key] = value
            path.write_text(yaml.safe_dump(record))
            with self.assertRaises(GateError):
                ba_gate(a.path, self.approvals)

    def test_symlink_artifact_or_runtime_paths_fail_closed(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "business-analysis.yaml").write_text(yaml.safe_dump(fixture()))
        target = self.root / BA_PATH
        target.symlink_to(outside / "business-analysis.yaml")
        with self.assertRaisesRegex(PipelineError, "Symlink"):
            Pipeline(self.root, FakeAgentRunner({}))
        target.unlink()
        (self.root / ".orchestrator").symlink_to(outside, target_is_directory=True)
        store = StateStore(self.root)
        with self.assertRaisesRegex(PipelineError, "Symlink"):
            with store.lock():
                self.fail("Must reject symlink runtime")

    def test_completed_run_resume_detects_staleness_without_agent_calls(self):
        p, runner = self.run_to_sa_approval(AgentResult(review={"status": "APPROVED", "findings": []}))
        self.assertEqual(p.resume().stage, Stage.DONE)
        count = len(runner.calls)
        (self.root / SA_PATH).write_bytes((self.root / SA_PATH).read_bytes() + b"\n")
        self.assertEqual(p.resume().status, "STALE")
        self.assertEqual(len(runner.calls), count)

    def test_git_branch_change_during_agent_prevents_promotion(self):
        def switch_branch(_):
            subprocess.run(["git", "-C", str(self.root), "switch", "-c", "main"], check=True, capture_output=True)
            return AgentResult({BA_PATH: yaml.safe_dump(fixture())})
        p = Pipeline(self.root, FakeAgentRunner({"business-analyst": switch_branch}))
        s = p.analyze()
        self.assertEqual(s.stage, Stage.FAILED)
        self.assertIn("Git HEAD/branch/worktree changed", s.reason)
        self.assertFalse((self.root / BA_PATH).exists())

    def test_event_log_symlink_cannot_write_external_file(self):
        store = StateStore(self.root)
        state = PipelineState("event-test", "requirements-to-architecture")
        directory = store.run_dir(state)
        directory.mkdir(parents=True)
        external = self.root / "unrelated.txt"
        external.write_text("Preserve me")
        (directory / "events.jsonl").symlink_to(external)
        with self.assertRaises(PipelineError):
            store.event(state, "test")
        self.assertEqual(external.read_text(), "Preserve me")


if __name__ == "__main__":
    unittest.main()
