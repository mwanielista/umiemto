#!/usr/bin/env python3
"""Live, model-attested role smoke test. Requires Python 3.11+ and Codex login."""
import argparse
import json
import pathlib
import subprocess
import sys
import tempfile
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[2]
ROLE_FILES = {
    "business-analyst": "business-analyst.toml",
    "system-analyst": "system-analyst.toml",
    "architect": "architect.toml",
    "architect-reviewer": "architecture-reviewer.toml",
}
ROLES = tuple(ROLE_FILES)


def check_report(report, definitions, events):
    if not isinstance(report, dict) or report.get("status") != "PASS":
        raise ValueError("Codex did not confirm successful role startup")
    results = report.get("roles", [])
    if not isinstance(results, list) or not all(isinstance(r, dict) for r in results):
        raise ValueError("Malformed role receipts")
    if len(results) != len(ROLES) or {r.get("role") for r in results} != set(ROLES):
        raise ValueError("Missing, duplicate or unexpected role receipts")
    children = set()
    for receipt in results:
        child = receipt.get("child", "")
        excerpt = receipt.get("instruction_excerpt", "")
        if not isinstance(child, str) or not child or child in children:
            raise ValueError("Missing or reused child identity")
        children.add(child)
        loaded = " ".join(definitions[receipt["role"]]["developer_instructions"].split())
        quoted = " ".join(excerpt.split()) if isinstance(excerpt, str) else ""
        if len(quoted) < 40 or quoted not in loaded:
            raise ValueError(f"Loaded instruction excerpt mismatch: {receipt['role']}")
    completed_wait = any(
        event.get("type") == "item.completed"
        and event.get("item", {}).get("type") == "collab_tool_call"
        and event["item"].get("tool") in ("wait", "waitAgent", "wait_agent")
        and event["item"].get("status") == "completed"
        for event in events
    )
    if not completed_wait:
        raise ValueError("No runtime evidence of waiting for child agents")
    if any(event.get("type") in ("error", "turn.failed") for event in events):
        raise ValueError("Runtime error reported")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    definitions = {}
    for role in ROLES:
        path = ROOT / ".codex/agents" / ROLE_FILES[role]
        definition = tomllib.loads(path.read_text())
        if definition.get("name") != role:
            raise ValueError(f"Unexpected agent name in {path.name}")
        definitions[role] = definition
    schema = {
        "type": "object", "additionalProperties": False,
        "properties": {
            "status": {"type": "string", "enum": ["PASS", "FAIL"]},
            "roles": {"type": "array", "items": {
                "type": "object", "additionalProperties": False,
                "properties": {
                    "role": {"type": "string", "enum": list(ROLES)},
                    "child": {"type": "string"},
                    "instruction_excerpt": {"type": "string"},
                }, "required": ["role", "child", "instruction_excerpt"],
            }},
        }, "required": ["status", "roles"],
    }
    prompt = """Run a read-only runtime smoke test, not business or architecture analysis.
Do not read repository files or edit anything. Use the custom-agent selector
exposed by your spawn tool to launch exactly one child of each of these types:
business-analyst, system-analyst, architect, architect-reviewer.
Use fork_turns none. Do not override model/reasoning or substitute default/worker.
Ask each child ONLY to identify its role and quote one exact, distinctive sentence
(at least 40 characters) from its loaded ROLE-SPECIFIC developer instructions.
It must not read files or use tools; do not supply any sentence or role instructions
to the child yourself. This checks instruction injection, not analysis quality.
Wait for all four child completions through the collaboration wait tool.
Return each actual child identity and its verbatim sentence using the output schema.
Return FAIL if any role is unavailable, any spawn fails, or a child does not finish.
Do not imitate a missing role or manufacture receipts. Close children after waiting.
"""
    with tempfile.TemporaryDirectory(prefix="eszkola-role-smoke-") as directory:
        schema_path = pathlib.Path(directory) / "response.schema.json"
        schema_path.write_text(json.dumps(schema))
        # Keep user configuration: it carries project trust and role discovery.
        # Do not use --ephemeral: this CLI needs parent thread state for spawning.
        command = ["codex", "exec", "--strict-config", "--json", "--sandbox",
                   "read-only", "--cd", str(ROOT), "--output-schema", str(schema_path), prompt]
        run = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True,
                             text=True, timeout=args.timeout)
        if run.returncode:
            raise ValueError(f"Codex exited with code {run.returncode}; inspect local runtime configuration")
        events = [json.loads(line) for line in run.stdout.splitlines() if line.strip()]
        messages = [e["item"]["text"] for e in events if e.get("type") == "item.completed"
                    and e.get("item", {}).get("type") == "agent_message"]
        if not messages:
            raise ValueError("No final runtime report")
        check_report(json.loads(messages[-1]), definitions, events)
        print("Evidence: completed collaboration wait plus model-attested child receipts;")
        print("CLI events do not independently bind each receipt to a completed custom-role child.")
        for role in ROLES:
            print(f"PASS: {role} model-reported startup receipt matches configured instructions")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
