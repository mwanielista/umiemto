"""Source snapshots and owner decision conventions, not semantic inference."""
import difflib
from datetime import date

from .artifacts import digest_bytes, load_yaml
from .config import safe_path
from .exceptions import PipelineError
from .patches import ID, TEXT, STRINGS, check_schema, enum, obj

DECISION_PATH = "docs/business/product-decisions.yaml"
DECISION_SCHEMA = obj({"schema_version": {"type": "integer", "enum": [1]},
    "owner": enum("Michał Wanielista"),
    "decisions": {"type": "array", "maxItems": 1000, "items": obj({
        "id": ID, "status": enum("ACTIVE", "SUPERSEDED"), "decision": TEXT,
        "rationale": TEXT, "supersedes": STRINGS,
        "source": obj({"location": TEXT, "locator": TEXT}),
        "date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"}})}})

PRECEDENCE = ["current explicit business-owner decision (ACTIVE registry entries)",
              "current owner-maintained source", "historical source", "generated BA baseline"]
POLICY = """Apply impact only. Current explicit owner decisions outrank owner-maintained
sources, which outrank historical sources, which outrank generated BA. ACTIVE
entries replace conflicting legacy BA. SUPERSEDED entries are historical context
and cannot independently produce blockers. Do not request unavailable historical
files to reconfirm an explicit current decision. Preserve real unresolved questions;
resolve affected questions only with current evidence. No fabricated decisions,
old hashes, approvals, or inferred business semantics. Source removal needs impact
review, not automatic deletion of all requirements. Do not read unchanged whole
business sources or full history in incremental mode; the complete compact baseline,
changed-source text/diffs and all open questions are supplied for integrity.
"""


def decisions(root, raw=None):
    if raw is None:
        raw = safe_path(root, DECISION_PATH).read_bytes()
    data = load_yaml(raw)
    try:
        check_schema(data, DECISION_SCHEMA)
        ids = set()
        for entry in data["decisions"]:
            date.fromisoformat(entry["date"])
            if entry["id"] in ids:
                raise ValueError("Duplicate decision")
            ids.add(entry["id"])
    except (PipelineError, ValueError) as error:
        raise PipelineError("VALIDATION_FAILED: owner decision registry") from error
    return data


def source_snapshot(root, config):
    decisions(root)
    result = {}
    for relative in config.sources:
        path = safe_path(root, relative)
        if not path.is_file():
            raise PipelineError(f"VALIDATION_FAILED: Business source missing: {relative}")
        raw = path.read_bytes()
        # Reject generated artifacts even if renamed outside canonical paths.
        try:
            data = load_yaml(raw)
        except PipelineError:
            data = {}
        if data.get("artifact_type") in {"business_analysis", "system_analysis"}:
            raise PipelineError("INVALID_GENERATED_ARTIFACT: business source")
        result[relative] = digest_bytes(raw)
    return result


def delta(previous, current):
    if previous is None:
        return {"unknown": sorted(current), "added": [], "changed": [], "removed": [], "unchanged": []}
    return {"unknown": [], "added": sorted(current.keys() - previous.keys()),
            "removed": sorted(previous.keys() - current.keys()),
            "changed": sorted(p for p in current.keys() & previous.keys() if current[p] != previous[p]),
            "unchanged": sorted(p for p in current.keys() & previous.keys() if current[p] == previous[p])}


def changed_context(root, archive, previous, current):
    changes = delta(previous, current)
    texts = []
    for category in ("unknown", "added", "changed", "removed"):
        for path in changes[category]:
            old_digest = (previous or {}).get(path)
            new_digest = current.get(path)
            old = archive.source_bytes(old_digest).decode("utf-8") if old_digest else ""
            new = archive.source_bytes(new_digest).decode("utf-8") if new_digest else ""
            texts.append({"path": path, "change": category, "old_digest": old_digest,
                          "new_digest": new_digest, "text": new,
                          "diff": "".join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), fromfile="previous/" + path, tofile="current/" + path)) if old_digest else ""})
    return {"delta": changes, "changed_sources": texts}


def semantic_ba_diff(previous, current):
    """Exclude approval/formatting metadata; include all business sections."""
    ignored = {"revision", "status", "approval", "schema_version", "artifact_id", "artifact_type", "section_notes"}
    changes = {}
    for key in sorted(previous.data.keys() | current.data.keys()):
        old, new = previous.data.get(key), current.data.get(key)
        if key in ignored or old == new:
            continue
        if isinstance(old, list) and isinstance(new, list):
            before = {item["id"]: item for item in old}
            after = {item["id"]: item for item in new}
            changes[key] = {"added": [after[i] for i in sorted(after.keys() - before.keys())],
                            "removed": [before[i] for i in sorted(before.keys() - after.keys())],
                            "changed": [{"before": before[i], "after": after[i]}
                                        for i in sorted(before.keys() & after.keys()) if before[i] != after[i]]}
        else:
            changes[key] = {"before": old, "after": new}
    return changes
