from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


def now():
    return datetime.now(timezone.utc).isoformat()


class Stage(StrEnum):
    NOOP = "NOOP"
    BUSINESS_ANALYSIS = "BUSINESS_ANALYSIS"
    BA_APPROVAL = "BA_APPROVAL"
    SYSTEM_ANALYSIS = "SYSTEM_ANALYSIS"
    SA_APPROVAL = "SA_APPROVAL"
    ARCHITECTURE = "ARCHITECTURE"
    ARCHITECTURE_REVIEW = "ARCHITECTURE_REVIEW"
    ARCH_FIX = "ARCH_FIX"
    ARCH_VALIDATION = "ARCH_VALIDATION"
    DONE = "DONE"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"


@dataclass
class AgentResult:
    files: dict[str, str] = field(default_factory=dict)
    review: dict | None = None
    patch: dict | None = None


@dataclass
class PipelineState:
    run_id: str
    pipeline: str
    stage: str = Stage.BUSINESS_ANALYSIS
    status: str = "PENDING"
    attempt: int = 1
    started_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)
    reason: str | None = None
    inputs: dict = field(default_factory=dict)
    config_digest: str = ""
