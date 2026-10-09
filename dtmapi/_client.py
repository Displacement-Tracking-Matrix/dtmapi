"""
Shared HTTP plumbing for the DTM API clients.

Everything here was lifted out of ``dtmapi/api.py`` unchanged: the subscription
key handling, the ``Ocp-Apim-Subscription-Key`` header, the retry loop with
exponential backoff, and the response envelope handling. ``DTMApi`` and
``DTMHnaApi`` both inherit it, so a fix to the retry logic lands in both.

Two things are deliberately left as overridable hooks, because the HNA API is a
different service behind the same gateway:

* :meth:`BaseDTMClient._get_endpoint` — each client maps its own endpoint names.
* :meth:`BaseDTMClient._unwrap` — the displacement API wraps results in an
  ``isSuccess`` / ``result`` envelope. If HNA does too, it inherits this for
  free; if not, it overrides one small method instead of the whole fetch.

Logging is per-subclass: ``self._logger`` resolves to ``dtmapi.api`` for
``DTMApi`` and ``dtmapi.hna.api`` for ``DTMHnaApi``, so existing log
configuration and any ``caplog`` assertions keep working.
"""

import logging
import os
import time
from typing import Any, Dict, Optional, Union

import pandas as pd
import requests

from dtmapi.exceptions import (
    DTMApiRequestError,
    DTMApiResponseError,
    DTMApiTimeoutError,
    DTMAuthenticationError,
)


class BaseDTMClient:
    """Common request handling for DTM API clients. Not used directly."""

    DEFAULT_TIMEOUT = 30  # seconds
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1  # seconds

    #: Human-readable service name, used in error messages.
    SERVICE_NAME = "DTM API"

    #: Environment variable consulted when no key is passed to the constructor.
    #: Each client reads its own variable only — the two services have separate
    #: subscriptions, so falling back to another client's key would send the
    #: wrong credential and surface as an unexplained 401.
    ENV_KEY_NAME = "DTMAPI_SUBSCRIPTION_KEY"

    #: Exception classes raised by the shared fetch loop. Subclasses override
    #: these so the error names the service that failed. HNA's variants inherit
    #: from these, so existing ``except DTMApiTimeoutError`` handlers still fire.
    AUTH_ERROR = DTMAuthenticationError
    TIMEOUT_ERROR = DTMApiTimeoutError
    REQUEST_ERROR = DTMApiRequestError
    RESPONSE_ERROR = DTMApiResponseError

    def __init__(
        self,
        subscription_key: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
    ):
        """
        :param subscription_key: DTM API subscription key. Can also be set via
            the environment variable named by :attr:`ENV_KEY_NAME`.
        :type subscription_key: Optional[str]
        :param timeout: Request timeout in seconds (default: 30).
        :type timeout: Optional[int]
        :param max_retries: Maximum number of retry attempts for failed requests (default: 3).
        :type max_retries: Optional[int]
        :param retry_delay: Base delay in seconds between retries (default: 1). Uses exponential backoff.
        :type retry_delay: Optional[float]
        :raises DTMAuthenticationError: If no subscription key is provided.
        """
        self._logger = logging.getLogger(type(self).__module__)
        self._logger.debug(f"Initializing {type(self).__name__} client")

        self.subscription_key = subscription_key or os.getenv(self.ENV_KEY_NAME)
        if not self.subscription_key:
            self._logger.error("No subscription key provided")
            raise self.AUTH_ERROR(
                f"A {self.SERVICE_NAME} Subscription Key is required. "
                f"Provide it as an argument or set the {self.ENV_KEY_NAME} environment variable."
            )

        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.max_retries = max_retries if max_retries is not None else self.DEFAULT_MAX_RETRIES
        self.retry_delay = retry_delay if retry_delay is not None else self.DEFAULT_RETRY_DELAY

    def __repr__(self) -> str:
        # The key is never shown, so a logged or notebook-echoed client is safe.
        return f"{type(self).__name__}(subscription_key='***', timeout={self.timeout})"

    def _headers(self) -> Dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (compatible; DTMClient/2.0)",
            "Ocp-Apim-Subscription-Key": self.subscription_key,
        }

    def _get_endpoint(self, endpoint_type: str) -> str:
        """Map an endpoint name to a full URL. Implemented by each subclass."""
        raise NotImplementedError

    def _unwrap(self, data: Dict[str, Any]) -> Any:
        """
        Pull the payload out of an API response.

        The displacement API wraps results in ``isSuccess`` / ``result`` /
        ``errorMessages``. Subclasses whose service answers differently
        override this one method.

        :raises DTMApiResponseError: If the response reports failure.
        """
        if not data.get("isSuccess"):
            error_messages = data.get("errorMessages", [])
            error_message = error_messages[0] if error_messages else "Unknown API error"
            self._logger.error(f"API returned error: {error_message}")
            raise self.RESPONSE_ERROR(error_message, error_messages)
        return data["result"]

    def _is_retryable_error(self, exception: Exception) -> bool:
        """
        Determine if an error should trigger a retry.

        :param exception: The exception to check.
        :type exception: Exception
        :return: True if the error is retryable, False otherwise.
        :rtype: bool
        """
        if isinstance(exception, requests.Timeout):
            return True

        if isinstance(exception, requests.ConnectionError):
            return True

        if isinstance(exception, requests.HTTPError):
            if exception.response is not None:
                status_code = exception.response.status_code
                if status_code in [429, 500, 502, 503, 504]:
                    return True

        return False

    def _fetch_data(
        self,
        api_url: str,
        params: Optional[Dict[str, Any]] = None,
        to_pandas: bool = True,
        as_bytes: bool = False,
        unwrap: bool = True,
    ) -> Union[pd.DataFrame, Dict[str, Any], bytes]:
        """
        Fetch data from the specified API URL with given parameters.
        Implements retry logic with exponential backoff for transient errors.

        :param api_url: The API endpoint URL.
        :type api_url: str
        :param params: The query parameters for the API request.
        :type params: Dict[str, Any]
        :param to_pandas: If True, the data will be returned as a pandas DataFrame. Otherwise, it will be returned as a JSON object.
        :type to_pandas: bool
        :return: The data matching the specified criteria, either as a DataFrame or a JSON object.
        :rtype: Union[pd.DataFrame, Dict[str, Any]]
        :raises DTMApiTimeoutError: If the request times out.
        :raises DTMAuthenticationError: If authentication fails.
        :raises DTMApiResponseError: If the API returns an error response.
        :raises DTMApiRequestError: If the request fails for other reasons.
        """
        self._logger.debug(f"Fetching data from {api_url} with params={params}")
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    # Exponential backoff: delay * (2 ^ (attempt - 1))
                    delay = self.retry_delay * (2 ** (attempt - 1))
                    self._logger.info(
                        f"Retrying request (attempt {attempt + 1}/{self.max_retries + 1}) after {delay}s delay"
                    )
                    time.sleep(delay)

                response = requests.get(
                    api_url, params=params, headers=self._headers(), timeout=self.timeout
                )
                self._logger.debug(f"Received response: status={response.status_code}")
                response.raise_for_status()

                if as_bytes:
                    # File downloads: return the body untouched, no JSON parsing.
                    self._logger.info(
                        f"Successfully fetched {len(response.content)} bytes from {api_url}"
                    )
                    return response.content

                data = response.json()

                if not unwrap:
                    # Flat JSON responses (e.g. a download pointer) have no envelope.
                    self._logger.info(f"Successfully fetched a JSON object from {api_url}")
                    return data

                result = self._unwrap(data)
                result_count = len(result) if isinstance(result, list) else 1
                self._logger.info(f"Successfully fetched {result_count} records from {api_url}")
                return pd.DataFrame(result) if to_pandas else result

            except requests.Timeout as e:
                last_exception = e
                self._logger.warning(f"Request timed out after {self.timeout} seconds: {api_url}")
                if not self._is_retryable_error(e) or attempt >= self.max_retries:
                    self._logger.error(f"Request timed out after {self.timeout} seconds (no more retries)")
                    raise self.TIMEOUT_ERROR(
                        f"Request timed out after {self.timeout} seconds"
                    ) from e
            except requests.HTTPError as e:
                last_exception = e
                if e.response.status_code == 401 or e.response.status_code == 403:
                    self._logger.error(f"Authentication failed: {e.response.status_code}")
                    raise self.AUTH_ERROR(
                        f"Authentication failed: {e.response.status_code} {e.response.reason}. "
                        f"Check the key passed to {type(self).__name__} (or {self.ENV_KEY_NAME}) — "
                        f"the {self.SERVICE_NAME} has its own subscription, separate from other DTM services."
                    ) from e
                self._logger.warning(f"HTTP error: {e.response.status_code} {e.response.reason}")
                if not self._is_retryable_error(e) or attempt >= self.max_retries:
                    self._logger.error(f"HTTP error occurred (no more retries): {e.response.status_code}")
                    raise self.REQUEST_ERROR(
                        f"HTTP error occurred: {e.response.status_code} {e.response.reason}"
                    ) from e
            except requests.RequestException as e:
                last_exception = e
                self._logger.warning(f"Request failed: {e}")
                if not self._is_retryable_error(e) or attempt >= self.max_retries:
                    self._logger.error(f"Request failed (no more retries): {e}")
                    raise self.REQUEST_ERROR(f"API request failed: {e}") from e

        # This should not be reached, but just in case
        if last_exception:
            raise self.REQUEST_ERROR(
                f"API request failed after {self.max_retries} retries"
            ) from last_exception
