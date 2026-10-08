class PipelineError(Exception):
    """Actionable, fail-closed pipeline error."""


class ArtifactError(PipelineError):
    pass


class GateError(PipelineError):
    pass


class ApprovalError(GateError):
    pass


class AgentExecutionError(PipelineError):
    pass


class ValidationError(PipelineError):
    pass


class ConcurrencyError(PipelineError):
    pass
