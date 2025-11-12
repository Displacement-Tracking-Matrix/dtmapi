"""Custom exceptions for the DTM API client."""


class DTMApiError(Exception):
    """Base exception for DTM API errors."""

    pass


class DTMAuthenticationError(DTMApiError):
    """Raised when authentication with the API fails."""

    pass


class DTMApiResponseError(DTMApiError):
    """Raised when the API returns an error response."""

    def __init__(self, message: str, error_messages: list = None):
        """
        Initialize the exception.

        :param message: The error message.
        :type message: str
        :param error_messages: List of error messages from the API response.
        :type error_messages: list
        """
        super().__init__(message)
        self.error_messages = error_messages or []


class DTMApiRequestError(DTMApiError):
    """Raised when a request to the API fails."""

    pass


class DTMApiTimeoutError(DTMApiError):
    """Raised when a request to the API times out."""

    pass


class DTMApiVersionError(DTMApiError):
    """Raised when an invalid API version is specified."""

    pass
