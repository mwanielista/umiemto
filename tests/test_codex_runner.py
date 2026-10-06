import json
import io
import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from orchestrator.agents import CodexAgentRunner
from orchestrator.exceptions import AgentExecutionError
from orchestrator.progress import ConsoleProgress


class RunnerTest(unittest.TestCase):
    def setUp(self):
        self.runner = CodexAgentRunner(Path(__file__).resolve().parents[1])

    def process(self, report):
        event = {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(report)}}
        return SimpleNamespace(returncode=0, stdout=json.dumps(event), stderr="")

    def test_loads_role_instructions_and_read_only_policy(self):
        with patch.object(self.runner, "_execute", return_value=self.process({"files": [], "review": None})) as run:
            result = self.runner.run("system-analyst", "Test only", {})
            command = run.call_args.args[0]
            self.assertIn("read-only", command)
            self.assertIn("--ignore-user-config", command)
            self.assertIn('approval_policy="never"', command)
            self.assertIn("agents.enabled=false", command)
            contract = next(x for x in command if x.startswith("developer_instructions="))
            self.assertIn("Senior System Analyst", contract)
            self.assertEqual(result.files, {})

    def test_runtime_failure_redacts_provider_stderr(self):
        with patch.object(self.runner, "_execute", return_value=SimpleNamespace(returncode=1, stdout="", stderr="SECRET_VALUE")):
            with self.assertRaises(AgentExecutionError) as error:
                self.runner.run("business-analyst", "Test")
            self.assertNotIn("SECRET_VALUE", str(error.exception))

    def test_duplicate_proposals_are_rejected(self):
        report = {"files": [{"path": "a", "content": "one"}, {"path": "a", "content": "two"}], "review": None}
        with patch.object(self.runner, "_execute", return_value=self.process(report)):
            with self.assertRaisesRegex(AgentExecutionError, "Duplicate"):
                self.runner.run("architect", "Test")

    def test_runtime_error_events_fail_closed(self):
        response = self.process({"files": [], "review": None})
        response.stdout = json.dumps({"type": "turn.failed"}) + "\n" + response.stdout
        with patch.object(self.runner, "_execute", return_value=response):
            with self.assertRaises(AgentExecutionError):
                self.runner.run("architect-reviewer", "Test")

    def test_heartbeat_updates_before_process_finishes_and_keeps_stdout_private(self):
        updates = []
        runner = CodexAgentRunner(self.runner.root, timeout=2, progress=lambda *args: updates.append(args), progress_interval=0.02)
        process = runner._execute([sys.executable, "-c", "import sys,time; data=sys.stdin.read(); time.sleep(.12); print(data)"], "PRIVATE_PROMPT", "business-analyst")
        self.assertEqual(process.stdout.strip(), "PRIVATE_PROMPT")
        self.assertGreaterEqual(sum(u[3] == "running" for u in updates), 2)
        self.assertEqual(updates[-1][3], "finished")
        self.assertNotIn("PRIVATE_PROMPT", str(updates))

    def test_timeout_stops_child_and_reports_timeout(self):
        updates = []
        runner = CodexAgentRunner(self.runner.root, timeout=.06, progress=lambda *args: updates.append(args), progress_interval=.02)
        with self.assertRaises(subprocess.TimeoutExpired):
            runner._execute([sys.executable, "-c", "import time; time.sleep(30)"], "", "architect")
        self.assertEqual(updates[-1][3], "timeout")

    def test_interrupt_stops_process_and_reraises(self):
        real_popen = subprocess.Popen
        children = []
        def interrupted(*args, **kwargs):
            process = real_popen(*args, **kwargs)
            original = process.communicate
            calls = 0
            def communicate(*a, **kw):
                nonlocal calls
                calls += 1
                if calls == 1:
                    raise KeyboardInterrupt
                return original(*a, **kw)
            process.communicate = communicate
            children.append(process)
            return process
        updates = []
        runner = CodexAgentRunner(self.runner.root, progress=lambda *args: updates.append(args))
        with patch("orchestrator.agents.subprocess.Popen", side_effect=interrupted):
            with self.assertRaises(KeyboardInterrupt):
                runner._execute([sys.executable, "-c", "import time; time.sleep(30)"], "", "architect")
        self.assertIsNotNone(children[0].poll())
        self.assertEqual(updates[-1][3], "interrupted")

    def test_console_output_is_flushed_plain_text_for_redirected_output(self):
        stream = io.StringIO()
        progress = ConsoleProgress(stream)
        progress("business-analyst", 65, 900)
        progress("business-analyst", 67, 900, "finished")
        self.assertIn("BA — analiza biznesowa", stream.getvalue())
        self.assertIn("01:05", stream.getvalue())
        self.assertEqual(len(stream.getvalue().splitlines()), 2)
        self.assertNotIn("\033", stream.getvalue())


class IncrementalRunnerTest(unittest.TestCase):
    setUp = RunnerTest.setUp
    process = RunnerTest.process
    def test_incremental_response_schema_patch_only_and_full_transport_unchanged(self):
        from orchestrator.patches import patch_schema
        for agent, kind in (("business-analyst", "business_analysis"), ("system-analyst", "system_analysis")):
            report = {"schema_version": 1, "artifact_type": kind,
                      "base": {"artifact_id": "BA", "revision": 5, "content_digest": "sha256:" + "a" * 64}, "operations": []}
            def execute(command, prompt, role):
                schema = json.loads(Path(command[command.index("--output-schema") + 1]).read_text())
                self.assertEqual(schema, patch_schema(kind))
                contract = next(x for x in command if x.startswith("developer_instructions="))
                self.assertIn("return ONLY the strict JSON patch", contract)
                self.assertIn("read-only", command)
                return self.process(report)
            with patch.object(self.runner, "_execute", side_effect=execute):
                result = self.runner.run(agent, "Incremental", {"mode": "INCREMENTAL"})
                self.assertEqual(result.patch, report)
                self.assertEqual(result.files, {})
                self.assertIsNone(result.review)
            with patch.object(self.runner, "_execute", return_value=self.process({"files": [], "review": None})):
                with self.assertRaisesRegex(AgentExecutionError, "CODEX_INVALID_OUTPUT"):
                    self.runner.run(agent, "Incremental", {"mode": "INCREMENTAL"})

    def test_classified_failures_never_contain_raw_provider_messages(self):
        for returncode in (0, 1):
            response = self.process({"files": [], "review": None})
            response.returncode = returncode
            response.stderr = "SECRET_TOKEN authentication invalid api key"
            response.stdout = json.dumps({"type": "turn.failed", "error": {"message": "SECRET_TOKEN private request"}}) + "\n" + response.stdout
            with patch.object(self.runner, "_execute", return_value=response):
                with self.assertRaises(AgentExecutionError) as caught:
                    self.runner.run("business-analyst", "Test")
            self.assertNotIn("SECRET_TOKEN", str(caught.exception))
            self.assertIn("CODEX_EXIT_FAILED" if returncode else "CODEX_INVALID_OUTPUT", str(caught.exception))
        with patch.object(self.runner, "_execute", side_effect=subprocess.TimeoutExpired("codex", 1)):
            with self.assertRaisesRegex(AgentExecutionError, "CODEX_TIMEOUT"):
                self.runner.run("business-analyst", "Test")
        with patch.object(self.runner, "_execute", side_effect=OSError("SECRET_TOKEN")):
            with self.assertRaisesRegex(AgentExecutionError, "^CODEX_START_FAILED$"):
                self.runner.run("business-analyst", "Test")

    def test_large_streams_and_prompt_do_not_deadlock(self):
        runner = CodexAgentRunner(self.runner.root, timeout=5, progress_interval=.05)
        script = "import sys;sys.stdout.write('O'*1000000);sys.stdout.flush();sys.stderr.write('E'*1000000);sys.stderr.flush();data=sys.stdin.read();print(len(data))"
        result = runner._execute([sys.executable, "-c", script], "I" * 1000000, "business-analyst")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "O" * 1000000 + "1000000\n")
        self.assertEqual(result.stderr, "E" * 1000000)

    def test_timeout_and_interrupt_kill_descendant_process_group(self):
        import os
        import tempfile
        import time
        for interrupted in (False, True):
            with self.subTest(interrupted=interrupted), tempfile.TemporaryDirectory() as temporary:
                marker = Path(temporary) / "child.pid"
                heartbeat = Path(temporary) / "heartbeat"
                child_script = "import time;from pathlib import Path\nwhile True:\n Path(" + repr(str(heartbeat)) + ").write_text(str(time.monotonic()))\n time.sleep(.01)"
                script = ("import subprocess,sys,time;from pathlib import Path;"
                          f"child=subprocess.Popen([sys.executable,'-c',{child_script!r}]);"
                          f"Path({str(marker)!r}).write_text(str(child.pid));time.sleep(30)")
                runner = CodexAgentRunner(self.runner.root, timeout=.3, progress_interval=.05)
                processes = []
                popen = subprocess.Popen
                def wrapped(*args, **kwargs):
                    process = popen(*args, **kwargs)
                    processes.append(process)
                    original = process.communicate
                    def communicate(*a, **kw):
                        if interrupted and marker.exists() and heartbeat.exists():
                            raise KeyboardInterrupt
                        return original(*a, **kw)
                    process.communicate = communicate
                    return process
                with patch("orchestrator.agents.subprocess.Popen", side_effect=wrapped):
                    with self.assertRaises(KeyboardInterrupt if interrupted else subprocess.TimeoutExpired):
                        runner._execute([sys.executable, "-c", script], "", "architect")
                self.assertIsNotNone(processes[0].poll())
                child = int(marker.read_text())
                # ps is unavailable in the restricted environment. A live child
                # advances its heartbeat; a terminated/zombie child cannot.
                time.sleep(.1)
                last = heartbeat.read_bytes()
                time.sleep(.1)
                if heartbeat.read_bytes() != last:
                    os.kill(child, 9)
                    self.fail("Descendant survived group cleanup")

    def test_malformed_and_duplicate_json_is_classified(self):
        for stdout in ("SECRET_TOKEN invalid JSON", '{"type":"x","type":"y"}'):
            with patch.object(self.runner, "_execute", return_value=SimpleNamespace(returncode=0, stdout=stdout, stderr="")):
                with self.assertRaisesRegex(AgentExecutionError, "CODEX_INVALID_OUTPUT") as caught:
                    self.runner.run("business-analyst", "Test")
                self.assertNotIn("SECRET_TOKEN", str(caught.exception))
