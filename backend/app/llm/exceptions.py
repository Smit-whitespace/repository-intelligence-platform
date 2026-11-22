"""Model configuration exceptions."""


class ModelConfigurationError(Exception):
    """The model configuration is invalid or cannot be used (HTTP 400).

    The message always says what to change, for example which
    environment variable to set.
    """


class ModelCompatibilityError(ModelConfigurationError):
    """No configured model can perform the requested operation."""
