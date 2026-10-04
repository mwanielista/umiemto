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
