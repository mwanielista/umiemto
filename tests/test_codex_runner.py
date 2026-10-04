import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from orchestrator.agents import CodexAgentRunner
from orchestrator.exceptions import AgentExecutionError


class RunnerTest(unittest.TestCase):
    def setUp(self):
        self.runner = CodexAgentRunner(Path(__file__).resolve().parents[1])

    def process(self, report):
        event = {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(report)}}
        return SimpleNamespace(returncode=0, stdout=json.dumps(event), stderr="")

    def test_loads_role_instructions_and_read_only_policy(self):
        with patch("orchestrator.agents.subprocess.run", return_value=self.process({"files": [], "review": None})) as run:
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
        with patch("orchestrator.agents.subprocess.run", return_value=SimpleNamespace(returncode=1, stdout="", stderr="SECRET_VALUE")):
            with self.assertRaises(AgentExecutionError) as error:
                self.runner.run("business-analyst", "Test")
            self.assertNotIn("SECRET_VALUE", str(error.exception))

    def test_duplicate_proposals_are_rejected(self):
        report = {"files": [{"path": "a", "content": "one"}, {"path": "a", "content": "two"}], "review": None}
        with patch("orchestrator.agents.subprocess.run", return_value=self.process(report)):
            with self.assertRaisesRegex(AgentExecutionError, "Duplicate"):
                self.runner.run("architect", "Test")

    def test_runtime_error_events_fail_closed(self):
        response = self.process({"files": [], "review": None})
        response.stdout = json.dumps({"type": "turn.failed"}) + "\n" + response.stdout
        with patch("orchestrator.agents.subprocess.run", return_value=response):
            with self.assertRaises(AgentExecutionError):
                self.runner.run("architect-reviewer", "Test")
