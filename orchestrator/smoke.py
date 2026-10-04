"""Explicit live Codex transport smoke; never creates BA/SA or approvals."""
import argparse
import sys
import tomllib
from pathlib import Path

from .agents import CodexAgentRunner, ROLE_FILES
from .exceptions import PipelineError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    runner = CodexAgentRunner(root, timeout=args.timeout)
    try:
        for role, filename in ROLE_FILES.items():
            task = "This is a transport smoke test ONLY. Do not use tools, read repository files, perform analysis or change anything. Identify your role and quote one exact distinctive sentence of at least 40 characters from your loaded role-specific developer instructions. "
            if role == "architect-reviewer":
                task += "Return files=[] and review APPROVED with one LOW finding id SMOKE-001, requirements=[], files=[], description containing only that exact quoted sentence, expected_action='Smoke only; no action'."
            else:
                task += "Return review=null, files=[{path:'role-receipt.txt', content:the exact quoted sentence}]. The controller will not promote this smoke receipt."
            result = runner.run(role, task, {"mode": "transport_smoke"})
            excerpt = result.review["findings"][0]["description"] if role == "architect-reviewer" else result.files["role-receipt.txt"]
            definition = tomllib.loads((root / ".codex/agents" / filename).read_text())
            quote = " ".join(excerpt.split())
            if len(quote) < 40 or quote not in " ".join(definition["developer_instructions"].split()):
                raise PipelineError(f"{role}: instruction receipt mismatch")
            print(f"PASS: {role}: contract-loaded read-only Codex transport", flush=True)
        print("No live business analysis, human approvals or product architecture produced.")
        return 0
    except (PipelineError, KeyError, TypeError, IndexError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
