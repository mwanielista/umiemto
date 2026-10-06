import copy
import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from orchestrator.agents import CodexAgentRunner, FakeAgentRunner
from orchestrator.artifacts import load_artifact
from orchestrator.cli import approve
from orchestrator.exceptions import ConcurrencyError, GateError, PipelineError
from orchestrator.models import AgentResult, Stage
from orchestrator.pipeline import BA_PATH, Pipeline
from orchestrator.provenance import ProvenanceStore
from orchestrator.sources import changed_context
from orchestrator.state import atomic_create
from tests import test_orchestrator as support


class ProvenanceIntegrityTest(unittest.TestCase):
    setUp = support.FactoryTest.setUp
    write = support.FactoryTest.write
    approve_artifact = support.FactoryTest.approve

    def bootstrap(self):
        runner = FakeAgentRunner({"business-analyst": AgentResult({BA_PATH: yaml.safe_dump(support.fixture())})})
        pipeline = Pipeline(self.root, runner)
        self.assertEqual(pipeline.analyze().stage, Stage.BA_APPROVAL)
        return pipeline, runner, load_artifact(self.root / BA_PATH)

    def test_noop_resume_rejects_replaced_approved_baseline(self):
        pipeline, runner, draft = self.bootstrap()
        original = self.approve_artifact(draft)
        pipeline.store.reset()
        self.assertEqual(pipeline.analyze().stage, Stage.NOOP)
        changed = copy.deepcopy(original.data)
        changed.update(revision=2, status="READY_FOR_REVIEW", approval=None, scope="Unrelated approved content")
        self.approve_artifact(self.write(BA_PATH, changed))
        with self.assertRaisesRegex(GateError, "pinned baseline changed"):
            pipeline.resume()
        self.assertEqual(len(runner.calls), 1)
        self.assertEqual(pipeline.store.load().stage, Stage.NOOP)

    def test_approval_stage_rejects_replaced_analysis(self):
        pipeline, runner, draft = self.bootstrap()
        changed = copy.deepcopy(draft.data)
        changed.update(revision=2, scope="Unrelated content")
        replacement = self.approve_artifact(self.write(BA_PATH, changed))
        state = pipeline.resume()
        self.assertEqual(state.stage, Stage.BA_APPROVAL)
        self.assertIn("pinned baseline changed", state.reason)
        self.assertEqual(len(runner.calls), 1)
        with self.assertRaises(GateError):
            approve(pipeline, "ba", "OWNER", confirm=lambda _: "y", output=lambda _: None)
        self.assertEqual(replacement.path.read_bytes(), replacement.raw)

    def test_noop_allows_metadata_only_approval_then_normal_gates(self):
        pipeline, runner, draft = self.bootstrap()
        pipeline.store.reset()
        self.assertEqual(pipeline.analyze().stage, Stage.NOOP)
        approved = self.approve_artifact(draft)
        runner.results["system-analyst"] = lambda _: AgentResult({
            "docs/requirements/system-analysis.yaml": yaml.safe_dump(support.fixture("system_analysis", approved))})
        self.assertEqual(pipeline.resume().stage, Stage.SA_APPROVAL)

    def test_source_capture_race_fails_before_inference(self):
        pipeline, runner, baseline = self.bootstrap()
        pipeline.store.reset()
        capture = pipeline.source_snapshot
        source = self.root / "AGENTS.md"
        def changed_capture():
            result = capture()
            source.write_bytes(source.read_bytes() + b"\nchanged during capture\n")
            return result
        with patch.object(pipeline, "source_snapshot", side_effect=changed_capture):
            with self.assertRaises(ConcurrencyError):
                pipeline.analyze()
        self.assertEqual(len(runner.calls), 1)
        self.assertEqual(baseline.path.read_bytes(), baseline.raw)
        self.assertIsNone(pipeline.store.load())

    def test_changed_context_reads_verified_blob_not_live_file(self):
        archive = ProvenanceStore(self.root)
        old = archive.source(b"Original source\n")
        current = archive.source(b"Pinned change\n")
        (self.root / "AGENTS.md").write_text("Transient unpinned content")
        context = changed_context(self.root, archive, {"AGENTS.md": old}, {"AGENTS.md": current})
        entry = context["changed_sources"][0]
        self.assertEqual(entry["text"], "Pinned change\n")
        self.assertNotIn("Transient", entry["diff"])
        archive.path("sources", current, "bin").write_bytes(b"corrupt")
        with self.assertRaisesRegex(PipelineError, "corrupted source"):
            changed_context(self.root, archive, {"AGENTS.md": old}, {"AGENTS.md": current})

    def test_full_context_uses_archived_snapshot_during_transient_change(self):
        source = self.root / "AGENTS.md"
        original = source.read_bytes()
        def proposal(context):
            self.assertEqual(context["source_texts"]["AGENTS.md"], original.decode())
            source.write_bytes(original)
            return AgentResult({BA_PATH: yaml.safe_dump(support.fixture())})
        pipeline = Pipeline(self.root, FakeAgentRunner({"business-analyst": proposal}))
        baseline = pipeline.baseline
        calls = 0
        def transient(*args):
            nonlocal calls
            calls += 1
            result = baseline(*args)
            if calls == 2:
                source.write_text("Transient unpinned content")
            return result
        with patch.object(pipeline, "baseline", side_effect=transient):
            self.assertEqual(pipeline.analyze().stage, Stage.BA_APPROVAL)

    def test_immutable_publication_interrupt_does_not_poison_final_path(self):
        destination = self.root / ".orchestrator/provenance/test.bin"
        with patch("orchestrator.state.os.fsync", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                atomic_create(destination, b"complete")
        self.assertFalse(destination.exists())
        self.assertEqual(list(destination.parent.glob(".pending-*")), [])
        atomic_create(destination, b"complete")
        with self.assertRaises(FileExistsError):
            atomic_create(destination, b"replacement")
        self.assertEqual(destination.read_bytes(), b"complete")

    def test_missing_approval_sidecar_requires_explicit_reconfirmation(self):
        pipeline, runner, draft = self.bootstrap()
        draft = load_artifact(pipeline.root / BA_PATH)
        candidate = pipeline.approvals.candidate(draft, "OWNER")
        with patch("orchestrator.approvals.atomic_create", side_effect=OSError("interrupted publication")):
            with self.assertRaises(OSError):
                pipeline.approvals.commit(draft, candidate)
        orphan = load_artifact(draft.path)
        self.assertEqual(orphan.digest, candidate.digest)
        self.assertFalse(pipeline.approvals.path(orphan).exists())
        self.assertEqual(pipeline.resume().stage, Stage.BA_APPROVAL)
        self.assertEqual(len(runner.calls), 1)
        approve(pipeline, "ba", "OWNER", confirm=lambda _: "y", output=lambda _: None)
        confirmed = load_artifact(draft.path)
        pipeline.approvals.validate(confirmed)
        pipeline.assert_analysis_candidate(pipeline.store.load(), confirmed, "ba")

    def test_successful_codex_exit_cleans_descendant_with_closed_pipes(self):
        heartbeat = self.root / "heartbeat"
        marker = self.root / "child.pid"
        child_script = ("import time;from pathlib import Path\nwhile True:\n "
                        f"Path({str(heartbeat)!r}).write_text(str(time.monotonic()))\n time.sleep(.01)")
        parent_script = ("import subprocess,sys,time;from pathlib import Path;"
                         f"child=subprocess.Popen([sys.executable,'-c',{child_script!r}], "
                         "stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);"
                         f"Path({str(marker)!r}).write_text(str(child.pid));time.sleep(.15)")
        runner = CodexAgentRunner(self.root, timeout=3, progress_interval=.02)
        result = runner._execute([sys.executable, "-c", parent_script], "", "architect")
        self.assertEqual(result.returncode, 0)
        try:
            before = heartbeat.read_bytes()
            time.sleep(.1)
            self.assertEqual(heartbeat.read_bytes(), before)
        finally:
            try:
                os.kill(int(marker.read_text()), 9)
            except ProcessLookupError:
                pass
