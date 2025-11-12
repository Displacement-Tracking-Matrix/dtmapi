"""Unit tests for custom exceptions."""

import unittest

from dtmapi.exceptions import (
    DTMApiError,
    DTMApiRequestError,
    DTMApiResponseError,
    DTMApiTimeoutError,
    DTMAuthenticationError,
)


class TestExceptions(unittest.TestCase):
    """Test custom exception classes."""

    def test_base_exception(self):
        """Test DTMApiError base exception."""
        with self.assertRaises(DTMApiError):
            raise DTMApiError("Base error")

    def test_authentication_error(self):
        """Test DTMAuthenticationError."""
        with self.assertRaises(DTMAuthenticationError) as context:
            raise DTMAuthenticationError("Auth failed")
        self.assertEqual(str(context.exception), "Auth failed")
        self.assertIsInstance(context.exception, DTMApiError)

    def test_response_error(self):
        """Test DTMApiResponseError."""
        error_messages = ["Error 1", "Error 2"]
        with self.assertRaises(DTMApiResponseError) as context:
            raise DTMApiResponseError("Response error", error_messages)
        self.assertEqual(str(context.exception), "Response error")
        self.assertEqual(context.exception.error_messages, error_messages)
        self.assertIsInstance(context.exception, DTMApiError)

    def test_response_error_without_messages(self):
        """Test DTMApiResponseError without error messages."""
        with self.assertRaises(DTMApiResponseError) as context:
            raise DTMApiResponseError("Response error")
        self.assertEqual(context.exception.error_messages, [])

    def test_request_error(self):
        """Test DTMApiRequestError."""
        with self.assertRaises(DTMApiRequestError) as context:
            raise DTMApiRequestError("Request failed")
        self.assertEqual(str(context.exception), "Request failed")
        self.assertIsInstance(context.exception, DTMApiError)

    def test_timeout_error(self):
        """Test DTMApiTimeoutError."""
        with self.assertRaises(DTMApiTimeoutError) as context:
            raise DTMApiTimeoutError("Timeout")
        self.assertEqual(str(context.exception), "Timeout")
        self.assertIsInstance(context.exception, DTMApiError)

    def test_exception_inheritance(self):
        """Test that all custom exceptions inherit from DTMApiError."""
        exceptions = [
            DTMAuthenticationError("test"),
            DTMApiResponseError("test"),
            DTMApiRequestError("test"),
            DTMApiTimeoutError("test"),
        ]
        for exc in exceptions:
            self.assertIsInstance(exc, DTMApiError)


if __name__ == "__main__":
    unittest.main()
