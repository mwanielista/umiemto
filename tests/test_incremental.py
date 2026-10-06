import copy
import json
import shutil
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from orchestrator.agents import CodexAgentRunner, FakeAgentRunner
from orchestrator.artifacts import Artifact, digest_bytes, load_artifact, validate_artifact
from orchestrator.cli import main, status
from orchestrator.config import Config
from orchestrator.exceptions import AgentExecutionError, GateError, PipelineError
from orchestrator.gates import ba_gate, sa_gate
from orchestrator.models import AgentResult, Stage
from orchestrator.patches import apply_patch, check_schema, patch_schema, serialize
from orchestrator.pipeline import BA_PATH, SA_PATH, Pipeline
from orchestrator.sources import DECISION_PATH, DECISION_SCHEMA, delta
from tests import test_orchestrator as support


def make_patch(artifact, operations=None):
    return {"schema_version": 1, "artifact_type": artifact.data["artifact_type"],
            "base": artifact.identity, "operations": operations or []}


def patch_result(context):
    return AgentResult(patch={"schema_version": 1, "artifact_type": context["baseline"]["artifact_type"],
                              "base": context["baseline_identity"], "operations": []})


class IncrementalTest(unittest.TestCase):
    setUp = support.FactoryTest.setUp
    write = support.FactoryTest.write
    approve = support.FactoryTest.approve

    def bootstrap(self):
        runner = FakeAgentRunner({"business-analyst": AgentResult({BA_PATH: yaml.safe_dump(support.fixture())})})
        pipeline = Pipeline(self.root, runner)
        self.assertEqual(pipeline.analyze().stage, Stage.BA_APPROVAL)
        self.assertEqual(runner.calls[0][2]["mode"], "FULL")
        return pipeline, runner, load_artifact(self.root / BA_PATH)

    def reset(self, pipeline):
        with pipeline.store.lock():
            pipeline.store.reset()

    def change_source(self):
        path = self.root / "docs/biznesplan-platforma-kursy-dla-dzieci.md"
        path.write_text(path.read_text() + "\nCurrent owner clarification for fixture.\n")
        return str(path.relative_to(self.root))

    def test_first_full_one_source_incremental_noop_and_full_override(self):
        p, runner, first = self.bootstrap()
        self.reset(p)
        changed = self.change_source()
        runner.results["business-analyst"] = patch_result
        self.assertEqual(p.analyze().stage, Stage.BA_APPROVAL)
        second = load_artifact(first.path)
        self.assertEqual(second.revision, 2)
        context = runner.calls[-1][2]
        self.assertEqual(context["mode"], "INCREMENTAL")
        self.assertEqual(context["delta"]["changed"], [changed])
        self.assertEqual([x["path"] for x in context["changed_sources"]], [changed])
        self.assertNotIn("source_texts", context)
        self.assertEqual(context["baseline_identity"], first.identity)
        self.assertIsNone(second.data["approval"])
        self.reset(p)
        self.assertEqual(p.analyze().stage, Stage.NOOP)
        self.assertEqual(p.analyze().status, "NOOP")
        self.assertEqual(len(runner.calls), 2)
        self.assertEqual(first.path.read_bytes(), second.raw)
        self.assertIn("PIPELINE: NOOP", status(p))
        d = copy.deepcopy(second.data)
        d["revision"] = 3
        runner.results["business-analyst"] = AgentResult({BA_PATH: yaml.safe_dump(d)})
        self.assertEqual(p.analyze(full=True).stage, Stage.BA_APPROVAL)
        self.assertEqual(runner.calls[-1][2]["mode"], "FULL")
        self.assertEqual(load_artifact(first.path).revision, 3)

    def test_active_run_not_replaced_even_full(self):
        p, runner, first = self.bootstrap()
        for full in (False, True):
            with self.assertRaisesRegex(PipelineError, "Run already exists"):
                p.analyze(full=full)
        self.assertEqual(len(runner.calls), 1)
        self.assertEqual(p.resume().stage, Stage.BA_APPROVAL)
        self.assertEqual(first.path.read_bytes(), first.raw)

    def test_legacy_revision5_unknown_adoption_preserves_exact_bytes(self):
        shutil.copyfile(Path(__file__).resolve().parents[1] / BA_PATH, self.root / BA_PATH)
        before = load_artifact(self.root / BA_PATH)
        runner = FakeAgentRunner({"business-analyst": patch_result})
        p = Pipeline(self.root, runner)
        self.assertEqual(p.analyze().stage, Stage.BLOCKED)
        context = runner.calls[-1][2]
        self.assertEqual(context["mode"], "INCREMENTAL")
        self.assertEqual(context["delta"]["unknown"], sorted(p.config.sources))
        self.assertTrue(all(c["old_digest"] is None for c in context["changed_sources"]))
        historical = p.archive.load(before.identity, before.path)
        self.assertEqual(historical.raw, before.raw)
        self.assertEqual(p.archive.get(historical)["source_snapshot"], "UNKNOWN")
        self.assertEqual(load_artifact(before.path).revision, 6)
        self.assertEqual(context["open_questions"], [q for q in before.open_questions if q["status"] == "OPEN"])

    def test_approval_normalization_archive_and_noop_after_reset(self):
        p, runner, draft = self.bootstrap()
        approved = self.approve(draft)
        self.assertNotEqual(approved.digest, draft.digest)
        self.assertEqual(p.archive.get(approved)["sources"], p.archive.get(draft)["sources"])
        self.assertEqual(p.archive.get(approved)["parent"], draft.identity)
        self.reset(p)
        self.assertEqual(p.analyze().stage, Stage.NOOP)
        self.assertEqual(len(runner.calls), 1)
        self.assertEqual(p.archive.load(draft.identity, draft.path).raw, draft.raw)
        self.assertEqual(p.archive.load(approved.identity, approved.path).raw, approved.raw)
        self.assertTrue(self.approvals.validate(approved))
        self.assertTrue(list((self.root / ".orchestrator/provenance/approvals").glob("*.yaml")))
        self.change_source()
        runner.results["business-analyst"] = patch_result
        self.assertEqual(p.analyze().stage, Stage.BA_APPROVAL)
        updated = load_artifact(draft.path)
        self.assertEqual(updated.revision, 2)
        self.assertIsNone(updated.data["approval"])
        with self.assertRaises(GateError):
            ba_gate(updated.path, self.approvals)
        self.approve(updated)
        self.assertTrue(self.approvals.path(approved).exists())

    def test_sa_incremental_uses_archived_approved_ba_and_requires_new_approval(self):
        p, runner, first = self.bootstrap()
        ba1 = self.approve(first)
        runner.results["system-analyst"] = lambda c: AgentResult({SA_PATH: yaml.safe_dump(support.fixture("system_analysis", ba1))})
        self.assertEqual(p.resume().stage, Stage.SA_APPROVAL)
        sa1 = self.approve(load_artifact(self.root / SA_PATH), ba1)
        self.reset(p)
        self.change_source()
        def updated(c):
            requirement = copy.deepcopy(c["baseline"]["business_requirements"][0])
            requirement["description"] = "Updated behavior from current owner source"
            return AgentResult(patch={"schema_version": 1, "artifact_type": "business_analysis", "base": c["baseline_identity"],
                                     "operations": [{"op": "update", "section": "business_requirements", "entry": requirement}]})
        runner.results["business-analyst"] = updated
        self.assertEqual(p.analyze().stage, Stage.BA_APPROVAL)
        ba2 = self.approve(load_artifact(first.path))
        with self.assertRaises(GateError):
            sa_gate(sa1.path, ba2.path, self.approvals)
        runner.results["system-analyst"] = patch_result
        self.assertEqual(p.resume().stage, Stage.SA_APPROVAL)
        context = runner.calls[-1][2]
        self.assertEqual(context["mode"], "INCREMENTAL")
        self.assertEqual(context["consumed_ba_identity"], ba1.identity)
        self.assertEqual(context["business_input"], ba2.identity)
        self.assertIn("business_requirements", context["semantic_ba_diff"])
        sa2 = load_artifact(sa1.path)
        self.assertEqual(sa2.data["business_input"], ba2.identity)
        self.assertEqual(sa2.revision, 2)
        self.assertIsNone(sa2.data["approval"])
        with self.assertRaisesRegex(GateError, "MISSING"):
            sa_gate(sa2.path, ba2.path, self.approvals)
        self.assertEqual(p.resume().stage, Stage.SA_APPROVAL)
        self.approve(sa2, ba2)
        self.assertEqual(sa_gate(sa2.path, ba2.path, self.approvals).revision, 2)
        self.assertEqual(p.archive.load(ba1.identity, ba1.path).raw, ba1.raw)

    def test_sa_patch_dangling_br_is_atomic(self):
        p, runner, first = self.bootstrap()
        ba = self.approve(first)
        runner.results["system-analyst"] = lambda _: AgentResult({SA_PATH: yaml.safe_dump(support.fixture("system_analysis", ba))})
        p.resume()
        old = load_artifact(self.root / SA_PATH)
        self.reset(p)
        self.change_source()
        runner.results["business-analyst"] = patch_result
        p.analyze()
        self.approve(load_artifact(first.path))
        def bad(c):
            entry = copy.deepcopy(c["baseline"]["functional_requirements"][0])
            entry["br_refs"] = ["BR-999"]
            return AgentResult(patch={"schema_version": 1, "artifact_type": "system_analysis", "base": c["baseline_identity"],
                                     "operations": [{"op": "update", "section": "functional_requirements", "entry": entry}]})
        runner.results["system-analyst"] = bad
        self.assertEqual(p.resume().stage, Stage.FAILED)
        self.assertEqual(old.path.read_bytes(), old.raw)

    def test_invalid_patch_and_runner_errors_preserve_canonical(self):
        for failure in ("wrong_revision", "wrong_digest", "malformed", "missing", "duplicate", "timeout", "full_yaml"):
            with self.subTest(failure=failure):
                # Each failure case needs independent immutable provenance.
                self.setUp()
                p, runner, baseline = self.bootstrap()
                self.reset(p)
                self.change_source()
                result = make_patch(baseline)
                if failure == "wrong_revision":
                    result["base"]["revision"] += 1
                elif failure == "wrong_digest":
                    result["base"]["content_digest"] = "sha256:" + "f" * 64
                elif failure == "malformed":
                    result["operations"] = [{"op": "set_approval", "value": "FORGED"}]
                elif failure == "missing":
                    result["operations"] = [{"op": "update", "section": "business_requirements", "entry": {**baseline.data["business_requirements"][0], "id": "BR-999"}}]
                elif failure == "duplicate":
                    result["operations"] = [{"op": "create", "section": "business_requirements", "entry": baseline.data["business_requirements"][0]}]
                def run(_):
                    if failure == "timeout":
                        raise AgentExecutionError("CODEX_TIMEOUT")
                    return AgentResult(patch=result)
                runner.results["business-analyst"] = run
                if failure == "full_yaml":
                    runner.results["business-analyst"] = AgentResult({BA_PATH: "revision: [unterminated"})
                state = p.analyze(full=failure == "full_yaml")
                self.assertEqual(state.stage, Stage.FAILED)
                self.assertEqual(baseline.path.read_bytes(), baseline.raw)
                codes = {"wrong_revision": "BASE_REVISION_MISMATCH", "wrong_digest": "BASE_DIGEST_MISMATCH",
                         "timeout": "CODEX_TIMEOUT", "full_yaml": "INVALID_GENERATED_ARTIFACT"}
                self.assertIn(codes.get(failure, "INVALID_PATCH"), state.reason)
                self.reset(p)
                baseline.path.unlink()

    def test_invalid_or_missing_baseline_selects_full(self):
        for raw in (b"key: [unterminated", b"revision: 1\n"):
            (self.root / BA_PATH).write_bytes(raw)
            runner = FakeAgentRunner({"business-analyst": AgentResult({BA_PATH: yaml.safe_dump(support.fixture())})})
            p = Pipeline(self.root, runner)
            self.assertEqual(p.analyze().stage, Stage.BA_APPROVAL)
            self.assertEqual(runner.calls[-1][2]["mode"], "FULL")
            self.reset(p)
        (self.root / BA_PATH).unlink()
        self.bootstrap()

    def test_removed_and_added_sources_and_input_change(self):
        p, runner, first = self.bootstrap()
        self.reset(p)
        source = "docs/szablon-programu-edukacyjnego-modul-4-zajecia.md"
        cfg = yaml.safe_load((self.root / "config/pipeline.yaml").read_bytes())
        cfg["business_sources"].remove(source)
        cfg["business_sources"].append("docs/business/new-source.md")
        old_text = (self.root / source).read_text()
        (self.root / source).unlink()
        (self.root / "docs/business/new-source.md").write_text("Current owner source")
        (self.root / "config/pipeline.yaml").write_text(yaml.safe_dump(cfg))
        runner.results["business-analyst"] = patch_result
        # Reuse the controller to verify it reloads changed configuration.
        self.assertEqual(p.analyze().stage, Stage.BA_APPROVAL)
        context = runner.calls[-1][2]
        self.assertEqual(context["delta"]["removed"], [source])
        self.assertEqual(context["delta"]["added"], ["docs/business/new-source.md"])
        removed = next(c for c in context["changed_sources"] if c["path"] == source)
        self.assertEqual(removed["old_digest"], digest_bytes(old_text.encode()))
        self.assertIsNone(removed["new_digest"])
        self.assertEqual(removed["text"], "")
        self.assertIn("-", removed["diff"])
        self.reset(p)
        role = self.root / ".codex/agents/business-analyst.toml"
        role.write_text(role.read_text() + "\n# Updated role input\n")
        self.assertEqual(p.analyze().stage, Stage.BA_APPROVAL)
        self.assertEqual(runner.calls[-1][2]["changed_sources"], [])
        self.assertEqual(runner.calls[-1][2]["mode"], "INCREMENTAL")

    def test_decisions_precedence_context_and_generated_source_rejection(self):
        p, runner, first = self.bootstrap()
        self.reset(p)
        decision = {"id": "DEC-001", "status": "ACTIVE", "decision": "All retakes are free",
                    "rationale": "Current explicit owner decision", "supersedes": ["legacy fee rule"],
                    "source": {"location": "Owner statement", "locator": "2026-10-06"}, "date": "2026-10-06"}
        self.write(DECISION_PATH, {"schema_version": 1, "owner": "Michał Wanielista", "decisions": [decision, {**decision, "id": "DEC-002", "status": "SUPERSEDED"}]})
        runner.results["business-analyst"] = patch_result
        self.assertEqual(p.analyze().stage, Stage.BA_APPROVAL)
        context = runner.calls[-1][2]
        self.assertEqual(context["delta"]["changed"], [DECISION_PATH])
        self.assertIn("current explicit", context["source_precedence"][0])
        self.assertIn("SUPERSEDED", context["source_policy"])
        self.assertIn("cannot independently produce blockers", context["source_policy"])
        self.assertEqual(context["owner_decisions"]["decisions"][0], decision)
        self.reset(p)
        cfg = yaml.safe_load((self.root / "config/pipeline.yaml").read_bytes())
        for source in (BA_PATH, SA_PATH, "docs/business/disguised.yaml", "docs/business/disguised.md"):
            with self.subTest(source=source):
                cfg["business_sources"].append(source)
                (self.root / "config/pipeline.yaml").write_text(yaml.safe_dump(cfg))
                if "disguised" in source:
                    self.write(source, support.fixture())
                    with self.assertRaisesRegex(PipelineError, "INVALID_GENERATED_ARTIFACT"):
                        Pipeline(self.root, runner).analyze()
                else:
                    with self.assertRaisesRegex(PipelineError, "INVALID_GENERATED_ARTIFACT"):
                        Config(self.root)
                cfg["business_sources"].pop()

    def test_retirement_survives_reset_approval_and_full_reanalysis(self):
        p, runner, first = self.bootstrap()
        self.reset(p)
        self.change_source()
        def retire(c):
            return AgentResult(patch={"schema_version": 1, "artifact_type": "business_analysis", "base": c["baseline_identity"],
                                     "operations": [{"op": "remove", "section": "business_requirements", "id": "BR-001"}]})
        runner.results["business-analyst"] = retire
        self.assertEqual(p.analyze().stage, Stage.BA_APPROVAL)
        retired = self.approve(load_artifact(first.path))
        self.assertIn("BR-001", p.archive.get(retired)["retired_ids"])
        self.reset(p)
        d = copy.deepcopy(retired.data)
        d.update(revision=3, status="READY_FOR_REVIEW", approval=None)
        d["business_requirements"] = first.data["business_requirements"]
        runner.results["business-analyst"] = AgentResult({BA_PATH: yaml.safe_dump(d)})
        self.assertEqual(p.analyze(full=True).stage, Stage.FAILED)
        self.assertEqual(retired.path.read_bytes(), retired.raw)
        self.assertIn("retired", p.store.load().reason)

    def test_resume_and_approval_detect_changed_inputs_in_same_controller(self):
        from orchestrator.cli import approve
        p, runner, first = self.bootstrap()
        role = self.root / ".codex/agents/business-analyst.toml"
        role.write_text(role.read_text() + "\n# Changed analysis contract\n")
        with self.assertRaisesRegex(PipelineError, "changed"):
            approve(p, "ba", "OWNER", confirm=lambda _: "y", output=lambda _: None)
        self.assertEqual(first.path.read_bytes(), first.raw)
        self.assertEqual(p.resume().stage, Stage.FAILED)
        self.assertEqual(len(runner.calls), 1)

    def test_full_malformed_yaml_missing_baseline_does_not_create_artifact(self):
        runner = FakeAgentRunner({"business-analyst": AgentResult({BA_PATH: "key: [unterminated"})})
        p = Pipeline(self.root, runner)
        self.assertEqual(p.analyze().stage, Stage.FAILED)
        self.assertIn("INVALID_GENERATED_ARTIFACT", p.store.load().reason)
        self.assertFalse((self.root / BA_PATH).exists())

    def test_noop_resume_preserves_approval_gate_and_reuses_unchanged_sa(self):
        p, runner, first = self.bootstrap()
        self.reset(p)
        self.assertEqual(p.analyze().stage, Stage.NOOP)
        self.assertEqual(p.resume().stage, Stage.BA_APPROVAL)
        self.assertEqual(len(runner.calls), 1)
        ba = self.approve(first)
        runner.results["system-analyst"] = lambda c: AgentResult({SA_PATH: yaml.safe_dump(support.fixture("system_analysis", ba))})
        self.assertEqual(p.resume().stage, Stage.SA_APPROVAL)
        old_sa = load_artifact(self.root / SA_PATH)
        self.reset(p)
        self.assertEqual(p.analyze().stage, Stage.NOOP)
        self.assertEqual(p.resume().stage, Stage.SA_APPROVAL)
        self.assertEqual(len(runner.calls), 2)
        self.assertEqual(old_sa.path.read_bytes(), old_sa.raw)

    def test_unverifiable_historical_sa_input_falls_back_to_full(self):
        p, runner, first = self.bootstrap()
        ba1 = self.approve(first)
        runner.results["system-analyst"] = lambda c: AgentResult({SA_PATH: yaml.safe_dump(support.fixture("system_analysis", ba1))})
        p.resume()
        self.reset(p)
        self.change_source()
        runner.results["business-analyst"] = patch_result
        p.analyze()
        ba2 = self.approve(load_artifact(first.path))
        p.archive.path("artifacts", ba1.digest, "yaml").unlink()
        def generate(c):
            self.assertEqual(c["mode"], "FULL")
            d = support.fixture("system_analysis", ba2)
            d["revision"] = 2
            return AgentResult({SA_PATH: yaml.safe_dump(d)})
        runner.results["system-analyst"] = generate
        self.assertEqual(p.resume().stage, Stage.SA_APPROVAL)
        self.assertEqual(load_artifact(self.root / SA_PATH).data["business_input"], ba2.identity)

    def test_interrupt_marks_running_and_resume_never_replays(self):
        p, runner, first = self.bootstrap()
        self.reset(p)
        self.change_source()
        def interrupt(c):
            raise KeyboardInterrupt
        runner.results["business-analyst"] = interrupt
        with self.assertRaises(KeyboardInterrupt):
            p.analyze()
        self.assertEqual(p.store.load().status, "RUNNING")
        self.assertEqual(first.path.read_bytes(), first.raw)
        calls = len(runner.calls)
        self.assertEqual(p.resume().stage, Stage.HUMAN_REQUIRED)
        self.assertEqual(len(runner.calls), calls)

    def test_registry_is_strict_and_dates_explicit(self):
        data = {"schema_version": 1, "owner": "Michał Wanielista", "decisions": []}
        check_schema(data, DECISION_SCHEMA)
        for changed in ({**data, "approval": "FORGED"}, {**data, "owner": "Another owner"}, {**data, "decisions": [None]}):
            with self.assertRaises(PipelineError):
                check_schema(changed, DECISION_SCHEMA)

    def test_cli_full_switch_without_live_agent(self):
        with patch("orchestrator.cli.Pipeline") as pipeline, patch("orchestrator.cli.status", return_value="OK"):
            pipeline.return_value.analyze.return_value = type("State", (), {"status": "WAITING_FOR_APPROVAL", "stage": Stage.BA_APPROVAL})()
            self.assertEqual(main(["--root", str(self.root), "analyze", "--full"]), 0)
            pipeline.return_value.analyze.assert_called_once_with(full=True)


class PatchTest(unittest.TestCase):
    def setUp(self):
        self.data = support.fixture()
        self.base = Artifact(Path(BA_PATH), copy.deepcopy(self.data), serialize(self.data))

    def test_deterministic_all_or_none_and_control_fields(self):
        operations = [{"op": "set_scope", "value": "New scope"}]
        patch_data = make_patch(self.base, operations)
        a, _ = apply_patch(self.base, patch_data)
        b, _ = apply_patch(self.base, patch_data)
        self.assertEqual(a.raw, b.raw)
        entry = self.data["business_requirements"][0]
        first, _ = apply_patch(self.base, make_patch(self.base, [{"op": "update", "section": "business_requirements", "entry": entry}]))
        second, _ = apply_patch(self.base, make_patch(self.base, [{"op": "update", "section": "business_requirements", "entry": dict(reversed(list(entry.items())))}]))
        self.assertEqual(first.raw, second.raw)
        self.assertEqual(self.base.data, self.data)
        self.assertEqual(a.revision, 2)
        self.assertIsNone(a.data["approval"])
        for injection in ("approval", "revision", "business_input", "files", "path"):
            invalid = copy.deepcopy(patch_data)
            invalid[injection] = "INJECTED"
            with self.assertRaisesRegex(PipelineError, "INVALID_PATCH"):
                apply_patch(self.base, invalid)
        for entry_field in ("approval", "technology_selection", "unexpected"):
            entry = {**self.data["business_requirements"][0], entry_field: "injected"}
            with self.assertRaisesRegex(PipelineError, "INVALID_PATCH"):
                apply_patch(self.base, make_patch(self.base, [{"op": "update", "section": "business_requirements", "entry": entry}]))
        self.assertEqual(self.base.data, self.data)

    def test_duplicate_creation_missing_update_and_retired_ids(self):
        entry = {**self.data["business_requirements"][0], "id": "BR-002"}
        create = {"op": "create", "section": "business_requirements", "entry": entry}
        for ops in ([create, create], [{"op": "update", "section": "business_requirements", "entry": entry}],
                    [create, {"op": "remove", "section": "business_requirements", "id": "BR-002"}, create]):
            with self.assertRaisesRegex(PipelineError, "INVALID_PATCH"):
                apply_patch(self.base, make_patch(self.base, ops))
        with self.assertRaisesRegex(PipelineError, "retired"):
            apply_patch(self.base, make_patch(self.base, [create]), retired=["BR-002"])
        removed, retired = apply_patch(self.base, make_patch(self.base, [{"op": "remove", "section": "business_requirements", "id": "BR-001"}]))
        self.assertIn("BR-001", retired)
        with self.assertRaisesRegex(PipelineError, "retired"):
            apply_patch(removed, make_patch(removed, [{"op": "create", "section": "business_requirements", "entry": self.data["business_requirements"][0]}]), retired=retired)

    def test_resolve_once_and_question_evidence_preserved(self):
        data = copy.deepcopy(self.data)
        data["status"] = "BLOCKED"
        data["open_questions"] = [{"id": "Q-001", "question": "Owner decision?", "severity": "BLOCKER", "owner": "owner",
                                    "affected_refs": ["BR-001"], "status": "OPEN", "resolution": None}]
        baseline = Artifact(self.base.path, data, serialize(data))
        resolve = {"op": "resolve_question", "id": "Q-001", "resolution": {"answer": "Actual owner answer", "evidence": "DEC-001"}}
        resolved, _ = apply_patch(baseline, make_patch(baseline, [resolve, {"op": "set_status", "value": "READY_FOR_REVIEW"}]))
        self.assertEqual(resolved.data["open_questions"][0]["status"], "RESOLVED")
        for artifact, ops in ((baseline, [resolve, resolve]), (resolved, [resolve]),
                              (baseline, [{**resolve, "id": "Q-999"}]),
                              (resolved, [{"op": "remove", "section": "open_questions", "id": "Q-001"}])):
            with self.assertRaisesRegex(PipelineError, "INVALID_PATCH"):
                apply_patch(artifact, make_patch(artifact, ops))
        self.assertEqual(baseline.data["open_questions"][0]["status"], "OPEN")

    def test_all_entry_schemas_closed_and_operation_bounds(self):
        for kind in ("business_analysis", "system_analysis"):
            schema = patch_schema(kind)
            def closed(node):
                if isinstance(node, dict):
                    if node.get("type") == "object":
                        self.assertFalse(node["additionalProperties"])
                    for v in node.values():
                        closed(v)
                elif isinstance(node, list):
                    for v in node:
                        closed(v)
            closed(schema)
        for ops in ([{"op": "replace", "path": "/approval", "value": "x"}],
                    [{"op": "set_scope", "value": "x"}] * 501,
                    [{"op": "set_status", "value": "APPROVED"}]):
            with self.assertRaisesRegex(PipelineError, "INVALID_PATCH"):
                apply_patch(self.base, make_patch(self.base, ops))

    def test_source_delta_includes_all_categories(self):
        self.assertEqual(delta({"old": "a", "same": "s", "changed": "a"}, {"new": "n", "same": "s", "changed": "b"}),
                         {"unknown": [], "added": ["new"], "removed": ["old"], "unchanged": ["same"], "changed": ["changed"]})


if __name__ == "__main__":
    unittest.main()
