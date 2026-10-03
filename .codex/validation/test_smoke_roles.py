"""Offline checks of fail-closed runtime report validation; no model usage."""
import copy
import unittest

from smoke_roles import ROLES, check_report


class RuntimeReportTests(unittest.TestCase):
    def setUp(self):
        self.definitions = {
            role: {"developer_instructions": f"Distinctive loaded instruction sentence for role {role}."}
            for role in ROLES
        }
        self.report = {"status": "PASS", "roles": [
            {"role": role, "child": f"/root/{role}",
             "instruction_excerpt": self.definitions[role]["developer_instructions"]}
            for role in ROLES
        ]}
        self.events = [{"type": "item.completed", "item": {
            "type": "collab_tool_call", "tool": "wait", "status": "completed"}}]

    def test_matching_report(self):
        check_report(self.report, self.definitions, self.events)

    def test_line_wrapping(self):
        self.definitions[ROLES[0]]["developer_instructions"] = self.definitions[ROLES[0]]["developer_instructions"].replace("sentence for", "sentence\nfor")
        check_report(self.report, self.definitions, self.events)

    def test_missing_role(self):
        self.report["roles"].pop()
        with self.assertRaises(ValueError):
            check_report(self.report, self.definitions, self.events)

    def test_failed_startup(self):
        self.report["status"] = "FAIL"
        with self.assertRaises(ValueError):
            check_report(self.report, self.definitions, self.events)

    def test_duplicate_child(self):
        self.report["roles"][1]["child"] = self.report["roles"][0]["child"]
        with self.assertRaises(ValueError):
            check_report(self.report, self.definitions, self.events)

    def test_wrong_instructions(self):
        self.report["roles"][0]["instruction_excerpt"] = "A fabricated instruction sentence that is absent from the configured role."
        with self.assertRaises(ValueError):
            check_report(self.report, self.definitions, self.events)

    def test_no_collaboration_evidence(self):
        with self.assertRaises(ValueError):
            check_report(self.report, self.definitions, [])

    def test_runtime_error(self):
        events = copy.deepcopy(self.events) + [{"type": "turn.failed"}]
        with self.assertRaises(ValueError):
            check_report(self.report, self.definitions, events)


if __name__ == "__main__":
    unittest.main()
