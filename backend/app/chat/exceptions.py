"""Chat subsystem exceptions."""


class ChatException(Exception):
    """Base chat exception."""


class ChatGenerationError(ChatException):
    """Raised when chat generation fails."""


class ChatProviderError(ChatException):
    """Raised when the chat provider fails."""


class ContextAssemblyError(ChatException):
    """Raised when context assembly fails."""