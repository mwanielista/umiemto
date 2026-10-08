import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from .exceptions import ArtifactError


class UniqueLoader(yaml.SafeLoader):
    """Reject duplicate keys instead of silently accepting the last value."""


def mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str) or key in result:
            raise ArtifactError(f"Duplicate or non-string YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)


def digest_bytes(content):
    return "sha256:" + hashlib.sha256(content).hexdigest()


def load_yaml(content):
    try:
        result = yaml.load(content, Loader=UniqueLoader)
        if not isinstance(result, dict):
            raise ArtifactError("YAML root must be an object")
        return result
    except (yaml.YAMLError, ValueError, TypeError, RecursionError) as error:
        raise ArtifactError(f"Malformed YAML: {error}") from error


@dataclass
class Artifact:
    path: Path
    data: dict
    raw: bytes

    @property
    def revision(self):
        return self.data.get("revision")

    @property
    def status(self):
        return self.data.get("status")

    @property
    def digest(self):
        return digest_bytes(self.raw)

    @property
    def open_questions(self):
        return self.data.get("open_questions", [])

    @property
    def blockers(self):
        return [q for q in self.open_questions if q["severity"] == "BLOCKER" and q["status"] == "OPEN"]

    @property
    def identity(self):
        return {"artifact_id": self.data["artifact_id"], "revision": self.revision,
                "content_digest": self.digest}


def load_artifact(path):
    path = Path(path)
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise ArtifactError(f"Required artifact unavailable: {path}: {error}") from error
    return Artifact(path, load_yaml(raw), raw)


def require(condition, message):
    if not condition:
        raise ArtifactError(message)


def text(value, label):
    require(isinstance(value, str) and bool(value.strip()), f"{label}: nonempty string required")


def strings(value, label, nonempty=True):
    require(isinstance(value, list) and (bool(value) or not nonempty), f"{label}: string array required")
    for item in value:
        text(item, label)


BA_SECTIONS = ("goals", "stakeholders", "actors", "processes", "business_requirements", "business_rules", "glossary")
SA_SECTIONS = ("functional_requirements", "non_functional_requirements", "system_actors", "use_cases", "domain_concepts", "data_requirements", "integrations", "edge_cases", "error_scenarios", "security_requirements", "br_coverage")


def validate_artifact(artifact, kind, ba=None):
    try:
        return _validate_artifact(artifact, kind, ba)
    except (TypeError, KeyError, ValueError, RecursionError) as error:
        raise ArtifactError(f"Malformed artifact structure: {error}") from error


def _validate_artifact(artifact, kind, ba=None):
    d = artifact.data
    require(type(d.get("schema_version")) is int and d["schema_version"] == 1, "schema_version must be 1")
    require(d.get("artifact_type") == kind, f"artifact_type must be {kind}")
    text(d.get("artifact_id"), "artifact_id")
    require(type(d.get("revision")) is int and d["revision"] > 0, "revision must be a positive integer")
    require(d.get("status") in {"DRAFT", "READY_FOR_REVIEW", "APPROVED", "BLOCKED"}, "Invalid artifact status")
    text(d.get("scope"), "scope")
    require("approval" in d, "approval field required (null until approved)")
    require(isinstance(d.get("section_notes"), dict), "section_notes object required")
    for value in d["section_notes"].values():
        text(value, "section_notes explanation")
    forbidden = {"architecture", "technology_selection", "implementation_tasks", "implementation_dag"}
    require(not forbidden.intersection(d), "Forbidden design/task section")
    ids = set()

    def entries(section, nonempty=False):
        value = d.get(section)
        require(isinstance(value, list), f"{section}: array required")
        require(not nonempty or bool(value), f"{section}: nonempty array required")
        if not value:
            text(d["section_notes"].get(section), f"section_notes.{section}")
        for entry in value:
            require(isinstance(entry, dict), f"{section}: object entries required")
            if section != "br_coverage":
                text(entry.get("id"), f"{section}.id")
                require(entry["id"] not in ids, f"Duplicate ID: {entry['id']}")
                ids.add(entry["id"])
        return value

    sources = entries("sources", True)
    source_ids = {s["id"] for s in sources}
    for s in sources:
        text(s.get("location"), "source.location")
        text(s.get("revision"), "source.revision")

    def refs(entry):
        r = entry.get("source_refs")
        require(isinstance(r, list) and bool(r), "Nonempty source_refs required")
        for ref in r:
            require(isinstance(ref, dict) and ref.get("source_id") in source_ids, "Unknown source reference")
            text(ref.get("locator"), "source locator")

    for section in ("assumptions", "constraints"):
        for e in entries(section):
            text(e.get("description"), section + ".description")
            refs(e)
    for q in entries("open_questions"):
        for key in ("question", "owner"):
            text(q.get(key), f"question.{key}")
        require(q.get("severity") in {"BLOCKER", "NON_BLOCKER"}, "Invalid question severity")
        require(q.get("status") in {"OPEN", "RESOLVED"}, "Invalid question status")
        strings(q.get("affected_refs"), "question.affected_refs")
        require("resolution" in q, "question.resolution required")
        if q["status"] == "OPEN":
            require(q["resolution"] is None, "Open question resolution must be null")
        else:
            require(isinstance(q["resolution"], dict), "Resolved question needs evidence")
            for key in ("answer", "evidence"):
                text(q["resolution"].get(key), "resolution." + key)
    require(not artifact.blockers or artifact.status == "BLOCKED", "Open BLOCKER requires BLOCKED status")
    if d["approval"] is not None:
        require(isinstance(d["approval"], dict), "approval must be null or object")
        for key in ("owner", "approved_at", "evidence"):
            text(d["approval"].get(key), "approval." + key)
        require(d["approval"].get("artifact_revision") == artifact.revision, "Embedded approval revision mismatch")
    if artifact.status == "APPROVED":
        require(d["approval"] is not None, "APPROVED requires approval metadata")

    sections = BA_SECTIONS if kind == "business_analysis" else SA_SECTIONS
    for section in sections:
        entries(section)
    requirement_sections = ("business_requirements",) if kind == "business_analysis" else ("functional_requirements", "non_functional_requirements")
    for section in requirement_sections:
        prefix = {"business_requirements": "BR", "functional_requirements": "FR", "non_functional_requirements": "NFR"}[section]
        for e in d[section]:
            require(re.fullmatch(prefix + r"-\d{3,}", e["id"]) is not None, f"Invalid {prefix} ID")
            for key in ("description", "rationale"):
                text(e.get(key), key)
            require(e.get("priority") in {"MUST", "SHOULD", "COULD"}, "Invalid priority")
            strings(e.get("acceptance_criteria"), "acceptance_criteria")
            refs(e)
    if kind == "business_analysis":
        actor_ids = {e["id"] for e in d["actors"]}
        for section in BA_SECTIONS:
            if section == "business_requirements":
                continue
            for e in d[section]:
                text(e.get("description"), section + ".description")
                refs(e)
                if section == "processes":
                    strings(e.get("actor_refs"), "process.actor_refs")
                    require(set(e["actor_refs"]) <= actor_ids, "Unknown process actor")
                    strings(e.get("steps"), "process.steps")
                if section == "glossary":
                    text(e.get("term"), "glossary.term")
    else:
        require(ba is not None, "SA validation requires BA")
        require(d.get("business_input") == ba.identity, f"STALE SA business_input; expected {ba.identity}, recorded {d.get('business_input')}. Regenerate SA.")
        br_ids = {e["id"] for e in ba.data["business_requirements"]}
        req_ids = {e["id"] for section in requirement_sections for e in d[section]}
        for section in requirement_sections:
            for e in d[section]:
                strings(e.get("br_refs"), "br_refs")
                require(set(e["br_refs"]) <= br_ids, f"Invalid BR traceability: {e['id']}")
        actor_ids = {e["id"] for e in d["system_actors"]}
        for section in SA_SECTIONS:
            if section in requirement_sections or section == "br_coverage":
                continue
            for e in d[section]:
                text(e.get("description"), section + ".description")
                strings(e.get("requirement_refs"), "requirement_refs")
                require(set(e["requirement_refs"]) <= req_ids, "Unknown supporting requirement reference")
                if section == "use_cases":
                    strings(e.get("actor_refs"), "use_case.actor_refs")
                    require(set(e["actor_refs"]) <= actor_ids, "Unknown use case actor")
                    for key in ("preconditions", "main_flow", "alternatives", "postconditions"):
                        strings(e.get(key), "use_case." + key, nonempty=key != "alternatives")
        covered = set()
        for e in d["br_coverage"]:
            require(e.get("br_id") in br_ids and e["br_id"] not in covered, "Unknown/duplicate BR coverage")
            covered.add(e["br_id"])
            strings(e.get("requirement_refs"), "coverage.requirement_refs", False)
            require(set(e["requirement_refs"]) <= req_ids, "Invalid coverage reference")
            require("exclusion_reason" in e, "coverage.exclusion_reason required")
            if not e["requirement_refs"]:
                text(e["exclusion_reason"], "coverage.exclusion_reason")
            for ref in e["requirement_refs"]:
                target = next(r for section in requirement_sections for r in d[section] if r["id"] == ref)
                require(e["br_id"] in target["br_refs"], "Coverage contradicts requirement br_refs")
        require(covered == br_ids, "Incomplete BR coverage")
    return artifact
