"""Custom exceptions for the Gemini Omni MCP server."""


class UltimateGeminiError(Exception):
    """Base exception for Gemini Omni MCP errors."""


class ConfigurationError(UltimateGeminiError):
    """Raised when there is a configuration error."""


class ValidationError(UltimateGeminiError):
    """Raised when input validation fails."""


class APIError(UltimateGeminiError):
    """Raised when an API request fails."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class AuthenticationError(APIError):
    """Raised when API authentication fails."""


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""


class ContentPolicyError(APIError):
    """Raised when content violates safety policies."""


class VideoProcessingError(UltimateGeminiError):
    """Raised when video processing fails."""


class FileOperationError(UltimateGeminiError):
    """Raised when file operations fail."""
