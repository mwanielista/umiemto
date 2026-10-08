from .artifacts import load_artifact, validate_artifact
from .exceptions import ArtifactError, GateError


def readiness(artifact):
    if artifact.blockers or artifact.status == "BLOCKED":
        raise GateError(f"BLOCKED {artifact.path.name}: {len(artifact.blockers)} unresolved blockers")
    if artifact.status not in {"READY_FOR_REVIEW", "APPROVED"}:
        raise GateError(f"{artifact.path.name} is {artifact.status}; complete analysis before progression")


def ba_gate(path, approvals, require_approval=True):
    try:
        artifact = validate_artifact(load_artifact(path), "business_analysis")
        readiness(artifact)
        if require_approval:
            approvals.validate(artifact)
        return artifact
    except (ArtifactError, GateError) as error:
        raise GateError(f"BA_GATE_FAILED\n{error}") from error


def sa_gate(path, ba_path, approvals, require_approval=True):
    try:
        ba = ba_gate(ba_path, approvals)
        artifact = validate_artifact(load_artifact(path), "system_analysis", ba)
        readiness(artifact)
        if require_approval:
            approvals.validate(artifact)
        return artifact
    except (ArtifactError, GateError) as error:
        raise GateError(f"SA_GATE_FAILED\n{error}") from error
