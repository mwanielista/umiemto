"""Content-addressed immutable archives, retained independently of run reset."""
import json
import re

from .artifacts import Artifact, digest_bytes, load_yaml
from .config import safe_path
from .exceptions import PipelineError
from .state import atomic_create


class ProvenanceStore:
    def __init__(self, root):
        self.root = root

    def path(self, category, digest, suffix):
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
            raise PipelineError("VALIDATION_FAILED: invalid archive digest")
        return safe_path(self.root, f".orchestrator/provenance/{category}/{digest[7:]}.{suffix}")

    @staticmethod
    def immutable(path, raw):
        if path.exists():
            if path.read_bytes() != raw:
                raise PipelineError("VALIDATION_FAILED: immutable archive collision")
            return
        try:
            atomic_create(path, raw)
        except FileExistsError:
            if path.read_bytes() != raw:
                raise PipelineError("VALIDATION_FAILED: immutable archive collision") from None

    def source(self, raw):
        digest = digest_bytes(raw)
        self.immutable(self.path("sources", digest, "bin"), raw)
        return digest

    def source_bytes(self, digest):
        raw = self.path("sources", digest, "bin").read_bytes()
        if digest_bytes(raw) != digest:
            raise PipelineError("VALIDATION_FAILED: corrupted source archive")
        return raw

    def get(self, artifact):
        path = self.path("manifests", artifact.digest, "json")
        if not path.exists():
            return None
        result = json.loads(path.read_bytes())
        expected = {"schema_version", "identity", "artifact_type", "source_snapshot", "sources", "input_digest", "parent", "retired_ids", "mode", "business_input"}
        if (not isinstance(result, dict) or set(result) != expected or result["schema_version"] != 1
                or result["artifact_type"] != artifact.data["artifact_type"]
                or result["source_snapshot"] not in {"KNOWN", "UNKNOWN"}
                or not isinstance(result["retired_ids"], list)
                or not all(isinstance(i, str) for i in result["retired_ids"])):
            raise PipelineError("VALIDATION_FAILED: malformed provenance")
        sources = result["sources"]
        if result["source_snapshot"] == "UNKNOWN":
            if sources is not None:
                raise PipelineError("VALIDATION_FAILED: unknown provenance snapshot")
        elif not isinstance(sources, dict):
            raise PipelineError("VALIDATION_FAILED: malformed source snapshot")
        else:
            for relative, digest in sources.items():
                safe_path(self.root, relative)
                self.path("sources", digest, "bin")
        if result.get("identity") != artifact.identity:
            raise PipelineError("VALIDATION_FAILED: provenance identity mismatch")
        archived = self.load(artifact.identity, artifact.path)
        if archived.raw != artifact.raw:
            raise PipelineError("VALIDATION_FAILED: provenance bytes mismatch")
        return result

    def record(self, artifact, sources=None, input_digest=None, parent=None, retired=(), mode="ADOPTED"):
        self.immutable(self.path("artifacts", artifact.digest, "yaml"), artifact.raw)
        manifest = {"schema_version": 1, "identity": artifact.identity,
                    "artifact_type": artifact.data["artifact_type"],
                    "source_snapshot": "UNKNOWN" if sources is None else "KNOWN",
                    "sources": sources, "input_digest": input_digest,
                    "parent": parent, "retired_ids": sorted(retired), "mode": mode,
                    "business_input": artifact.data.get("business_input")}
        raw = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
        self.immutable(self.path("manifests", artifact.digest, "json"), raw)
        return manifest

    def adopt(self, artifact):
        return self.get(artifact) or self.record(artifact)

    def approved(self, original, candidate):
        manifest = self.adopt(original)
        return self.record(candidate, manifest["sources"], manifest["input_digest"],
                           original.identity, manifest["retired_ids"], "APPROVAL")

    def load(self, identity, canonical_path):
        raw = self.path("artifacts", identity["content_digest"], "yaml").read_bytes()
        result = Artifact(canonical_path, load_yaml(raw), raw)
        if result.identity != identity:
            raise PipelineError("VALIDATION_FAILED: archived artifact mismatch")
        return result
