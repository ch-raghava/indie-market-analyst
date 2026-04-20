class AnalystError(Exception):
    """Base for all project-raised errors."""


class ProviderError(AnalystError):
    pass


class GuardrailViolation(AnalystError):
    pass


class ToolExecutionError(AnalystError):
    pass


class TopologyError(AnalystError):
    pass
