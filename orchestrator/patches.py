"""Versioned, bounded analysis patches. No JSON pointers or lifecycle fields."""
import copy
import re

import yaml

from .artifacts import Artifact, BA_SECTIONS, SA_SECTIONS, validate_artifact
from .exceptions import PipelineError


def obj(properties):
    return {"type": "object", "additionalProperties": False,
            "properties": properties, "required": list(properties)}


TEXT = {"type": "string", "minLength": 1, "maxLength": 20000}
ID = {"type": "string", "pattern": r"^[A-Za-z][A-Za-z0-9_-]{0,127}$"}
STRINGS = {"type": "array", "items": TEXT, "maxItems": 1000}
REFS = {"type": "array", "minItems": 1, "maxItems": 1000,
        "items": obj({"source_id": ID, "locator": TEXT})}
RESOLUTION = obj({"answer": TEXT, "evidence": TEXT})
IDENTITY = obj({"artifact_id": TEXT, "revision": {"type": "integer", "minimum": 1},
                "content_digest": {"type": "string", "pattern": r"^sha256:[0-9a-f]{64}$"}})


def enum(*values):
    return {"type": "string", "enum": list(values)}


def entry_schemas(kind):
    basic = {"id": ID, "description": TEXT, "source_refs": REFS}
    req = {**basic, "rationale": TEXT, "priority": enum("MUST", "SHOULD", "COULD"),
           "acceptance_criteria": {**STRINGS, "minItems": 1}}
    common = {
        "sources": obj({"id": ID, "location": TEXT, "revision": TEXT}),
        "assumptions": obj(basic), "constraints": obj(basic),
        "open_questions": obj({"id": ID, "question": TEXT, "severity": enum("BLOCKER", "NON_BLOCKER"),
                               "owner": TEXT, "affected_refs": {**STRINGS, "minItems": 1},
                               "status": enum("OPEN", "RESOLVED"),
                               "resolution": {"anyOf": [RESOLUTION, {"type": "null"}]}}),
    }
    if kind == "business_analysis":
        common.update({s: obj(basic) for s in BA_SECTIONS})
        common["business_requirements"] = obj({**req, "id": {**ID, "pattern": r"^BR-\d{3,}$"}})
        common["processes"] = obj({**basic, "actor_refs": {**STRINGS, "minItems": 1}, "steps": {**STRINGS, "minItems": 1}})
        common["glossary"] = obj({**basic, "term": TEXT})
    elif kind == "system_analysis":
        supporting = {"id": ID, "description": TEXT, "requirement_refs": {**STRINGS, "minItems": 1}}
        common.update({s: obj(supporting) for s in SA_SECTIONS})
        for s, prefix in (("functional_requirements", "FR"), ("non_functional_requirements", "NFR")):
            common[s] = obj({**req, "id": {**ID, "pattern": rf"^{prefix}-\d{{3,}}$"}, "br_refs": {**STRINGS, "minItems": 1}})
        common["use_cases"] = obj({**supporting, "actor_refs": {**STRINGS, "minItems": 1},
                                   **{k: {**STRINGS, "minItems": 1} for k in ("preconditions", "main_flow", "postconditions")},
                                   "alternatives": STRINGS})
        common["br_coverage"] = obj({"br_id": {**ID, "pattern": r"^BR-\d{3,}$"}, "requirement_refs": STRINGS,
                                     "exclusion_reason": {"anyOf": [TEXT, {"type": "null"}]}})
    else:
        raise PipelineError("INVALID_PATCH: artifact type")
    return common


def patch_schema(kind):
    operations = []
    for section, schema in entry_schemas(kind).items():
        for op in ("create", "update"):
            operations.append(obj({"op": enum(op), "section": enum(section), "entry": schema}))
        if section != "open_questions":
            operations.append(obj({"op": enum("remove"), "section": enum(section), "id": ID}))
    operations.extend([
        obj({"op": enum("resolve_question"), "id": ID, "resolution": RESOLUTION}),
        obj({"op": enum("set_scope"), "value": TEXT}),
        obj({"op": enum("set_section_note"), "section": enum(*entry_schemas(kind), "Changed", "Verification", "Architecture_impact", "Not_verified", "source_coverage", "handoff_gate"), "value": TEXT}),
        obj({"op": enum("set_status"), "value": enum("DRAFT", "READY_FOR_REVIEW", "BLOCKED")}),
    ])
    return obj({"schema_version": {"type": "integer", "enum": [1]}, "artifact_type": enum(kind),
                "base": IDENTITY, "operations": {"type": "array", "maxItems": 500, "items": {"anyOf": operations}}})


def check_schema(value, schema):
    """Validate the closed JSON Schema subset used by our transport, without deps."""
    def fail():
        raise PipelineError("INVALID_PATCH: schema violation")
    if "anyOf" in schema:
        for option in schema["anyOf"]:
            try:
                check_schema(value, option)
                return
            except PipelineError:
                pass
        fail()
    kind = schema.get("type")
    valid = {"object": isinstance(value, dict), "array": isinstance(value, list),
             "string": isinstance(value, str), "integer": type(value) is int,
             "null": value is None}
    if not valid.get(kind, False):
        fail()
    if "enum" in schema and value not in schema["enum"]:
        fail()
    if kind == "object":
        if set(value) != set(schema["properties"]):
            fail()
        for key, item in value.items():
            check_schema(item, schema["properties"][key])
    elif kind == "array":
        if not schema.get("minItems", 0) <= len(value) <= schema.get("maxItems", 1000):
            fail()
        for item in value:
            check_schema(item, schema["items"])
    elif kind == "string":
        if not schema.get("minLength", 0) <= len(value) <= schema.get("maxLength", 20000):
            fail()
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value):
            fail()
    elif kind == "integer" and value < schema.get("minimum", 0):
        fail()


def serialize(data):
    return yaml.safe_dump(data, sort_keys=True, allow_unicode=True, default_flow_style=False).encode("utf-8")


def entry_ids(data):
    return {("coverage:" + e["br_id"] if section == "br_coverage" else e["id"])
            for section, value in data.items() if isinstance(value, list)
            for e in value if isinstance(e, dict) and ("id" in e or section == "br_coverage")}


def validate_entries(data):
    """Strict entry shapes also apply to complete generated proposals."""
    sections = entry_schemas(data["artifact_type"])
    expected = set(sections) | {"schema_version", "artifact_type", "artifact_id", "revision", "status", "scope", "approval", "section_notes"}
    if data["artifact_type"] == "system_analysis":
        expected.add("business_input")
    if set(data) != expected:
        raise PipelineError("INVALID_PATCH: unexpected artifact fields")
    for section, schema in sections.items():
        for entry in data[section]:
            check_schema(entry, schema)


def apply_patch(baseline, patch, ba=None, retired=()):
    kind = baseline.data["artifact_type"]
    check_schema(patch, patch_schema(kind))
    if patch["base"]["artifact_id"] != baseline.identity["artifact_id"] or patch["base"]["revision"] != baseline.revision:
        raise PipelineError("BASE_REVISION_MISMATCH")
    if patch["base"]["content_digest"] != baseline.digest:
        raise PipelineError("BASE_DIGEST_MISMATCH")
    data = copy.deepcopy(baseline.data)
    unavailable = set(retired) | entry_ids(data)
    retired = set(retired)
    for operation in patch["operations"]:
        op = operation["op"]
        if op in {"create", "update", "remove"}:
            section = operation["section"]
            key = "br_id" if section == "br_coverage" else "id"
            identifier = operation.get("id") if op == "remove" else operation["entry"][key]
            identity_key = "coverage:" + identifier if section == "br_coverage" else identifier
            entries = data[section]
            target = next((e for e in entries if e[key] == identifier), None)
            if op == "create":
                if target is not None or identity_key in unavailable:
                    raise PipelineError("INVALID_PATCH: duplicate or retired ID")
                if section == "open_questions" and operation["entry"]["status"] != "OPEN":
                    raise PipelineError("INVALID_PATCH: create questions OPEN, then resolve")
                entries.append(copy.deepcopy(operation["entry"]))
                unavailable.add(identity_key)
            else:
                if target is None:
                    raise PipelineError("INVALID_PATCH: nonexistent entry")
                if op == "remove":
                    entries.remove(target)
                    retired.add(identity_key)
                else:
                    replacement = operation["entry"]
                    if section == "open_questions" and (replacement["status"] != target["status"] or replacement["resolution"] != target["resolution"]):
                        raise PipelineError("INVALID_PATCH: question lifecycle requires resolve_question")
                    entries[entries.index(target)] = copy.deepcopy(replacement)
        elif op == "resolve_question":
            target = next((q for q in data["open_questions"] if q["id"] == operation["id"]), None)
            if target is None or target["status"] != "OPEN":
                raise PipelineError("INVALID_PATCH: nonexistent or already resolved question")
            target.update(status="RESOLVED", resolution=copy.deepcopy(operation["resolution"]))
        elif op == "set_section_note":
            data["section_notes"][operation["section"]] = operation["value"]
        elif op == "set_scope":
            data["scope"] = operation["value"]
        elif op == "set_status":
            data["status"] = operation["value"]
    data["revision"] = baseline.revision + 1
    data["approval"] = None
    # Lifecycle metadata belongs to the controller. Never inherit approval.
    if data["status"] == "APPROVED":
        data["status"] = "READY_FOR_REVIEW"
    if ba is not None:
        data["business_input"] = ba.identity
    validate_entries(data)
    try:
        artifact = validate_artifact(Artifact(baseline.path, data, serialize(data)), kind, ba)
    except PipelineError as error:
        raise PipelineError("VALIDATION_FAILED: patched artifact contract") from error
    return artifact, sorted(retired)
