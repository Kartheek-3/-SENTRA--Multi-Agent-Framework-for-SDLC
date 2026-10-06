class ToolError(Exception):
    pass


class ToolRegistrationError(ToolError):
    pass


class ToolPermissionError(ToolError):
    pass


class ToolExecutionError(ToolError):
    pass


class ToolTimeoutError(ToolExecutionError):
    pass
