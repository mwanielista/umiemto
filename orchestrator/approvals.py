import copy
from datetime import datetime
from pathlib import Path

import yaml

from .artifacts import Artifact, digest_bytes, load_artifact, load_yaml, validate_artifact
from .exceptions import ApprovalError, ConcurrencyError
from .models import now
from .config import safe_path
from .state import atomic_write


class ApprovalStore:
    def __init__(self, root):
        self.root = Path(root)
        self.directory = self.root / ".orchestrator/approvals"

    def path(self, artifact):
        return safe_path(self.root, f".orchestrator/approvals/{artifact.data['artifact_type'].replace('_', '-')}-r{artifact.revision}.yaml")

    def validate(self, artifact):
        path = self.path(artifact)
        if not path.exists():
            short = "ba" if artifact.data["artifact_type"] == "business_analysis" else "sa"
            raise ApprovalError(f"MISSING approval for revision {artifact.revision}. Required action: factory approve {short}")
        try:
            record = load_yaml(path.read_bytes())
            identity = {"type": artifact.data["artifact_type"].upper(),
                        "path": str(artifact.path.relative_to(self.root)),
                        "artifact_id": artifact.data["artifact_id"], "revision": artifact.revision,
                        "digest": artifact.digest}
            if record.get("artifact") != identity:
                raise ApprovalError(f"INVALID approval: revision/digest/identity mismatch for {artifact.path.name}")
            approval = record.get("approval", {})
            timestamp = datetime.fromisoformat(approval.get("approved_at", ""))
            embedded = artifact.data.get("approval") or {}
            if (artifact.status != "APPROVED" or approval.get("status") != "APPROVED"
                    or not approval.get("approved_by") or timestamp.utcoffset() is None
                    or embedded.get("owner") != approval["approved_by"]
                    or embedded.get("approved_at") != approval["approved_at"]
                    or embedded.get("evidence") != str(path.relative_to(self.root))):
                raise ApprovalError("INVALID approval metadata")
        except (OSError, ValueError, TypeError, KeyError) as error:
            raise ApprovalError(f"INVALID approval record: {error}") from error
        return record

    def candidate(self, artifact, owner, ba=None):
        safe_path(self.root, str(artifact.path.relative_to(self.root)))
        validate_artifact(artifact, artifact.data["artifact_type"], ba)
        if artifact.status not in {"READY_FOR_REVIEW", "APPROVED"} or artifact.blockers:
            raise ApprovalError("Approval requires complete READY_FOR_REVIEW content without blockers")
        if not isinstance(owner, str) or not owner.strip():
            raise ApprovalError("Designated owner label required")
        data = copy.deepcopy(artifact.data)
        data["status"] = "APPROVED"
        data["approval"] = {"owner": owner, "approved_at": now(), "artifact_revision": artifact.revision,
                            "evidence": str(self.path(artifact).relative_to(self.root))}
        raw = yaml.safe_dump(data, sort_keys=False, allow_unicode=True).encode()
        return Artifact(artifact.path, data, raw)

    def commit(self, original, candidate):
        safe_path(self.root, str(original.path.relative_to(self.root)))
        if original.path != candidate.path or original.revision != candidate.revision:
            raise ApprovalError("Approval candidate identity changed")
        if load_artifact(original.path).digest != original.digest:
            raise ConcurrencyError("Artifact changed during confirmation; review again")
        path = self.path(candidate)
        if path.exists():
            # Approval for a content revision is immutable, including an invalid old record.
            raise ApprovalError("Approval record already exists. Changed content requires a new revision.")
        record = {"artifact": {"type": candidate.data["artifact_type"].upper(),
                               "artifact_id": candidate.data["artifact_id"],
                               "path": str(candidate.path.relative_to(self.root)),
                               "revision": candidate.revision, "digest": digest_bytes(candidate.raw)},
                  "approval": {"status": "APPROVED", "approved_by": candidate.data["approval"]["owner"],
                               "approved_at": candidate.data["approval"]["approved_at"]}}
        atomic_write(candidate.path, candidate.raw)
        # If interrupted between writes, an embedded APPROVED alone never passes a gate.
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(yaml.safe_dump(record, sort_keys=False).encode())
            stream.flush()
            import os
            os.fsync(stream.fileno())
        return record
