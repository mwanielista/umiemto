from pathlib import Path

from .artifacts import digest_bytes, load_yaml
from .exceptions import PipelineError


VALIDATORS = {
    ("python", "docs/architecture/validation/check_baseline.py"),
    ("python", "docs/architecture/validation/check_baseline.py", "--self-test"),
}
STAGES = {
    "business_analysis": ("business-analyst", "ba_approval"),
    "ba_approval": (None, "system_analysis"),
    "system_analysis": ("system-analyst", "sa_approval"),
    "sa_approval": (None, "architecture"),
    "architecture": ("architect", "architecture_review"),
    "architecture_review": ("architect-reviewer", "architecture_validation"),
    "arch_fix": ("architect", "architecture_review"),
    "architecture_validation": (None, "done"),
}


def safe_path(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise PipelineError(f"Unsafe repository path: {relative}")
    if str(Path(relative)) != relative:
        raise PipelineError(f"Noncanonical repository path: {relative}")
    root = Path(root).absolute()
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise PipelineError(f"Path escapes repository: {relative}")
    # Reject even in-repository symlinks; promotion must not write aliases.
    for part in (path, *path.parents):
        if part == root:
            break
        if part.is_symlink():
            raise PipelineError(f"Symlink path not supported: {relative}")
    return path


class Config:
    def __init__(self, root):
        self.root = Path(root)
        path = self.root / "config/pipeline.yaml"
        try:
            raw = path.read_bytes()
            self.data = load_yaml(raw)
        except OSError as error:
            raise PipelineError(f"Pipeline configuration unavailable: {error}") from error
        self.digest = digest_bytes(raw)
        d = self.data
        if d.get("version") != 1 or d.get("pipeline") != {"name": "requirements-to-architecture"}:
            raise PipelineError("Unsupported pipeline configuration")
        stages = d.get("stages", {})
        if not isinstance(stages, dict) or set(stages) != set(STAGES):
            raise PipelineError("v0.1 requires all configured mandatory stages")
        for name, (agent, next_stage) in STAGES.items():
            entry = stages[name]
            if not isinstance(entry, dict) or entry.get("agent") != agent or entry.get("next") != next_stage:
                raise PipelineError(f"Invalid stage/gate progression: {name}")
        for name, short in (("business_analysis", "ba"), ("system_analysis", "sa")):
            expected = f"docs/requirements/{name.replace('_', '-')}.yaml"
            if stages[name].get("artifact") != expected or stages[name].get("gate") != short + "_gate":
                raise PipelineError(f"Mandatory artifact/gate cannot be changed: {name}")
            safe_path(self.root, expected)
        retry = stages["architecture_review"].get("retry")
        if retry != {"stage": "arch_fix", "max_attempts": 3}:
            raise PipelineError("Exactly three architecture review attempts are required")
        validation = stages["architecture_validation"]
        if validation.get("type") != "command":
            raise PipelineError("Executable architecture validation required")
        self.commands = validation.get("commands")
        if not isinstance(self.commands, list) or not self.commands:
            raise PipelineError("Mandatory validators missing")
        for command in self.commands:
            if not isinstance(command, list) or not all(isinstance(arg, str) for arg in command) or tuple(command) not in VALIDATORS:
                raise PipelineError(f"Validator is not allowlisted: {command}")
        if set(map(tuple, self.commands)) != VALIDATORS:
            raise PipelineError("Both architecture validators are mandatory")
        self.sources = d.get("business_sources")
        if not isinstance(self.sources, list) or not self.sources:
            raise PipelineError("Business sources required")
        if not all(isinstance(source, str) for source in self.sources):
            raise PipelineError("Business source paths must be strings")
        if len(set(self.sources)) != len(self.sources):
            raise PipelineError("Duplicate business source")
        if "docs/business/product-decisions.yaml" not in self.sources:
            raise PipelineError("Owner decision registry must be configured")
        for source in self.sources:
            safe_path(self.root, source)
            if source.startswith((".orchestrator/", "docs/architecture/")) or source in {
                "docs/requirements/business-analysis.yaml", "docs/requirements/system-analysis.yaml"
            }:
                raise PipelineError("INVALID_GENERATED_ARTIFACT: business source")

    def agent(self, stage):
        return self.data["stages"][stage]["agent"]
