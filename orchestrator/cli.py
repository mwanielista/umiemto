import argparse
import json
import sys
from pathlib import Path

import yaml

from .agents import CodexAgentRunner
from .artifacts import load_artifact, validate_artifact
from .exceptions import PipelineError
from .config import safe_path
from .gates import ba_gate, sa_gate
from .models import Stage
from .pipeline import BA_PATH, SA_PATH, Pipeline
from .git_utils import inspect_git


def repository_root(start):
    path = Path(start).resolve()
    for candidate in (path, *path.parents):
        if (candidate / "AGENTS.md").is_file() and (candidate / "config/pipeline.yaml").is_file():
            return candidate
    raise PipelineError("Run factory inside the eSzkola repository")


def approve(pipeline, short, owner, confirm=input, output=print):
    with pipeline.store.lock():
        state = pipeline.store.load()
        expected = Stage.BA_APPROVAL if short == "ba" else Stage.SA_APPROVAL
        if not state or state.stage != expected:
            raise PipelineError(f"Approval requires active {expected} stage")
        git_context = inspect_git(pipeline.root)
        if git_context["branch"] in {"main", "master", ""}:
            raise PipelineError("Approval writes require the feature branch")
        if state.config_digest != pipeline.config.digest or state.inputs["sources"] != pipeline.source_snapshot():
            raise PipelineError("Configuration/business sources changed; reset analysis before approval")
        path = safe_path(pipeline.root, BA_PATH if short == "ba" else SA_PATH)
        ba = ba_gate(pipeline.root / BA_PATH, pipeline.approvals) if short == "sa" else None
        artifact = ba_gate(path, pipeline.approvals, False) if short == "ba" else sa_gate(path, pipeline.root / BA_PATH, pipeline.approvals, False)
        try:
            pipeline.approvals.validate(artifact)
            output("Approval already VALID for this exact artifact")
            return
        except PipelineError:
            pass
        candidate = pipeline.approvals.candidate(artifact, owner, ba)
        requirements = len(artifact.data.get("business_requirements", [])) if short == "ba" else len(artifact.data["functional_requirements"]) + len(artifact.data["non_functional_requirements"])
        output(f"{'Business' if short == 'ba' else 'System'} Analysis\nRevision: {artifact.revision}\nCurrent digest: {artifact.digest}\nStatus: {artifact.status}\nRequirements: {requirements}\nOpen questions: BLOCKER={len(artifact.blockers)} OTHER={sum(q['status'] == 'OPEN' and q['severity'] == 'NON_BLOCKER' for q in artifact.open_questions)}")
        output("Metadata-only candidate: status -> APPROVED; approval -> " + json.dumps(candidate.data["approval"]))
        output("Exact candidate digest: " + candidate.digest)
        output("Review the complete candidate content before confirming:\n" + candidate.raw.decode())
        if confirm("Approve this exact candidate revision? [y/N] ").strip().lower() != "y":
            output("Approval cancelled; nothing written")
            return
        if state.inputs["sources"] != pipeline.source_snapshot():
            raise PipelineError("Business sources changed during confirmation")
        pipeline.assert_git_identity(git_context)
        if ba:
            current_ba = ba_gate(pipeline.root / BA_PATH, pipeline.approvals)
            if current_ba.identity != ba.identity or state.inputs["ba"] != ba.identity:
                raise PipelineError("BA changed during SA approval; regenerate SA")
        record = pipeline.approvals.commit(artifact, candidate)
        pipeline.store.event(state, "human_approval", artifact=record["artifact"], approval=record["approval"])
        output("Approval saved. Continue with factory resume")


def status(pipeline):
    state = pipeline.store.load()
    lines = ["eSzkola Analysis & Architecture Pipeline", "Run: " + (state.run_id if state else "NONE")]
    ba = None
    for label, relative, kind in (("Business Analysis", BA_PATH, "business_analysis"), ("System Analysis", SA_PATH, "system_analysis")):
        lines.append("\n" + label)
        try:
            artifact = load_artifact(pipeline.root / relative)
            validate_artifact(artifact, kind, ba)
            if kind == "business_analysis":
                ba = artifact
            try:
                pipeline.approvals.validate(artifact)
                approval = "VALID"
            except PipelineError as error:
                approval = str(error)
            lines.extend([f"revision: {artifact.revision}", f"status: {artifact.status}", f"digest: {artifact.digest}",
                          f"blockers: {len(artifact.blockers)}", "approval: " + approval])
            if kind == "business_analysis":
                lines.append(f"requirements: {len(artifact.data['business_requirements'])}")
            else:
                lines.extend([f"functional reqs: {len(artifact.data['functional_requirements'])}",
                              f"non-functional reqs: {len(artifact.data['non_functional_requirements'])}",
                              "consumes BA: " + json.dumps(artifact.data["business_input"])])
        except PipelineError as error:
            lines.append("INVALID/MISSING/STALE: " + str(error))
    if state:
        directory = pipeline.store.run_dir(state)
        baseline_path = directory / "architecture-baseline.json"
        if baseline_path.exists():
            baseline = json.loads(baseline_path.read_text())
            lines.append("\nArchitecture baseline: " + baseline["head"])
            diff_path = directory / "architecture-diff.json"
            if diff_path.exists():
                changes = json.loads(diff_path.read_text())
                lines.extend("Changed: " + change["path"] for change in changes)
            from .git_utils import architecture_snapshot, snapshot
            current = architecture_snapshot(snapshot(pipeline.root))
            reviewed_path = directory / "reviewed-architecture.json"
            try:
                pipeline.check_inputs(state)
                if reviewed_path.exists() and current != json.loads(reviewed_path.read_text()):
                    raise PipelineError("Architecture content changed after review")
                lines.append("Architecture lineage: CURRENT")
            except PipelineError as error:
                lines.append("Architecture lineage: STALE: " + str(error))
        else:
            lines.append("\nArchitecture: NOT_STARTED")
        reviews = sorted(directory.glob("architecture-review-*.yaml"))
        for review_path in reviews:
            review = json.loads(review_path.read_text())
            lines.append(f"Architecture Review {review_path.stem.split('-')[-1]}: {review['status']}")
        if not reviews:
            lines.append("Architecture Review: NOT_STARTED")
        validation_path = directory / "validation-results.json"
        if validation_path.exists():
            for result in json.loads(validation_path.read_text()):
                lines.append(f"Validation {' '.join(result['command'])}: {'PASS' if result['returncode'] == 0 else 'FAIL'}")
        if state.stage in {Stage.BA_APPROVAL, Stage.SA_APPROVAL}:
            display = "WAITING_FOR_BA_APPROVAL" if state.stage == Stage.BA_APPROVAL else "WAITING_FOR_SA_APPROVAL"
        else:
            display = state.stage
        if state.reason:
            lines.append("Reason: " + state.reason)
        # DONE is historical; modified approved/reviewed content never displays current DONE.
        if state.stage == Stage.DONE and any("STALE:" in line or "INVALID/MISSING/STALE:" in line for line in lines):
            display = "STALE (persisted run completed previously)"
        lines.append("\nPIPELINE: " + display)
    else:
        lines.append("\nPIPELINE: NOT_STARTED")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Deterministic eSzkola analysis pipeline")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("analyze", "resume", "status", "reset", "history"):
        commands.add_parser(name)
    approval = commands.add_parser("approve")
    approval.add_argument("artifact", choices=("ba", "sa"))
    approval.add_argument("--owner", help="Designated human owner label; default BUSINESS_OWNER/REQUIREMENTS_OWNER")
    args = parser.parse_args(argv)
    try:
        root = repository_root(args.root)
        pipeline = Pipeline(root, CodexAgentRunner(root))
        if args.command == "approve":
            if not sys.stdin.isatty():
                raise PipelineError("Human approval requires an interactive terminal; no --yes or piped approval")
            approve(pipeline, args.artifact, args.owner or ("BUSINESS_OWNER" if args.artifact == "ba" else "REQUIREMENTS_OWNER"))
        elif args.command in {"analyze", "resume"}:
            state = getattr(pipeline, args.command)()
            print(status(pipeline))
            return 1 if state.status == "STALE" or state.stage in {Stage.FAILED, Stage.BLOCKED, Stage.HUMAN_REQUIRED} else 0
        elif args.command == "status":
            with pipeline.store.lock():
                print(status(pipeline))
        elif args.command == "reset":
            with pipeline.store.lock():
                pipeline.store.reset()
            print("Runtime state reset; artifacts, approvals and history retained")
        elif args.command == "history":
            with pipeline.store.lock():
                for run in sorted((pipeline.store.directory / "runs").glob("*/events.jsonl")):
                    print(run.read_text())
        return 0
    except (PipelineError, OSError, ValueError, TypeError, KeyError, EOFError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
