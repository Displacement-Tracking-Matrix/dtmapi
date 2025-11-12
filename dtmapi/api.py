import logging
import os
import time
from typing import Any, Dict, Optional, Union

import pandas as pd
import requests

from dtmapi.config import (
    COUNTRY_LIST_API,
    COUNTRY_LIST_API_V2,
    IDP_ADMIN_0_API,
    IDP_ADMIN_0_API_V2,
    IDP_ADMIN_1_API,
    IDP_ADMIN_1_API_V2,
    IDP_ADMIN_2_API,
    IDP_ADMIN_2_API_V2,
    OPERATION_LIST_API,
    OPERATION_LIST_API_V2,
)
from dtmapi.exceptions import (
    DTMApiRequestError,
    DTMApiResponseError,
    DTMApiTimeoutError,
    DTMAuthenticationError,
    DTMApiVersionError,
)
from dtmapi.validators import (
    ValidationError,
    validate_date_format,
    validate_date_range,
    validate_required_params,
    validate_round_number_range,
)

# Configure logger
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class DTMApi:
    """
    Python interface to DTM API endpoints. Supports both v2 (legacy) and v3 (current).
    Requires Ocp-Apim-Subscription-Key for authentication.

    **API Version Differences:**

    +-------------------------------+----------+----------+
    | Feature                       | v2       | v3       |
    +===============================+==========+==========+
    | IDP Admin 0, 1, 2 Data        | Yes      | Yes      |
    +-------------------------------+----------+----------+
    | Country List                  | Yes      | Yes      |
    +-------------------------------+----------+----------+
    | Operation List                | Yes      | Yes      |
    +-------------------------------+----------+----------+
    | Gender/Sex Disaggregation     | No       | **Yes**  |
    +-------------------------------+----------+----------+
    | Origin of Displacement        | No       | **Yes**  |
    +-------------------------------+----------+----------+
    | Displacement Reason           | No       | **Yes**  |
    +-------------------------------+----------+----------+
    | Status                        | Legacy   | Current  |
    +-------------------------------+----------+----------+

    **Usage Examples:**

    v3 API (default - recommended for new projects)::

        api = DTMApi(subscription_key="YOUR-KEY")
        data = api.get_idp_admin0_data(CountryName="Sudan")
        # Returns IDP data WITH gender, origin, and reason fields

    v2 API (legacy - for historical data compatibility)::

        api = DTMApi(subscription_key="YOUR-KEY", api_version="v2")
        data = api.get_idp_admin0_data(CountryName="Sudan")
        # Returns IDP data WITHOUT demographic disaggregation
    """

    DEFAULT_TIMEOUT = 30  # seconds
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1  # seconds

    def __init__(
        self,
        subscription_key: Optional[str] = None,
        api_version: str = "v3",
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
    ):
        """
        Initialize the DTM API client.

        :param subscription_key: DTM API subscription key. Can also be set via DTMAPI_SUBSCRIPTION_KEY env var.
        :type subscription_key: Optional[str]
        :param api_version: API version to use: "v2" (legacy) or "v3" (current, default).
        :type api_version: str
        :param timeout: Request timeout in seconds (default: 30).
        :type timeout: Optional[int]
        :param max_retries: Maximum number of retry attempts for failed requests (default: 3).
        :type max_retries: Optional[int]
        :param retry_delay: Base delay in seconds between retries (default: 1). Uses exponential backoff.
        :type retry_delay: Optional[float]
        :raises DTMAuthenticationError: If no subscription key is provided.
        :raises DTMApiVersionError: If api_version is not "v2" or "v3".
        """
        logger.debug("Initializing DTMApi client")

        # Validate API version
        if api_version not in ["v2", "v3"]:
            raise DTMApiVersionError(
                f"api_version must be 'v2' or 'v3', got: '{api_version}'"
            )
        self.api_version = api_version

        # Validate and set subscription key
        self.subscription_key = subscription_key or os.getenv("DTMAPI_SUBSCRIPTION_KEY")
        if not self.subscription_key:
            logger.error("No subscription key provided")
            raise DTMAuthenticationError(
                "A DTM API Subscription Key is required. "
                "Provide it as an argument or set the DTMAPI_SUBSCRIPTION_KEY environment variable."
            )

        # Set timeout and retry parameters
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.max_retries = max_retries if max_retries is not None else self.DEFAULT_MAX_RETRIES
        self.retry_delay = retry_delay if retry_delay is not None else self.DEFAULT_RETRY_DELAY

        logger.info(
            f"DTMApi client initialized with api_version={self.api_version}, "
            f"timeout={self.timeout}s, max_retries={self.max_retries}, "
            f"retry_delay={self.retry_delay}s"
        )

    def _headers(self) -> Dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (compatible; DTMClient/2.0)",
            "Ocp-Apim-Subscription-Key": self.subscription_key,
        }

    def _get_endpoint(self, endpoint_type: str) -> str:
        """
        Get the appropriate API endpoint URL based on the API version.

        :param endpoint_type: Type of endpoint ("admin0", "admin1", "admin2", "countries", "operations").
        :type endpoint_type: str
        :return: The full API endpoint URL.
        :rtype: str
        """
        endpoint_map = {
            "v3": {
                "admin0": IDP_ADMIN_0_API,
                "admin1": IDP_ADMIN_1_API,
                "admin2": IDP_ADMIN_2_API,
                "countries": COUNTRY_LIST_API,
                "operations": OPERATION_LIST_API,
            },
            "v2": {
                "admin0": IDP_ADMIN_0_API_V2,
                "admin1": IDP_ADMIN_1_API_V2,
                "admin2": IDP_ADMIN_2_API_V2,
                "countries": COUNTRY_LIST_API_V2,
                "operations": OPERATION_LIST_API_V2,
            },
        }
        return endpoint_map[self.api_version][endpoint_type]

    def _is_retryable_error(self, exception: Exception) -> bool:
        """
        Determine if an error should trigger a retry.

        :param exception: The exception to check.
        :type exception: Exception
        :return: True if the error is retryable, False otherwise.
        :rtype: bool
        """
        # Retry on timeout
        if isinstance(exception, requests.Timeout):
            return True

        # Retry on connection errors
        if isinstance(exception, requests.ConnectionError):
            return True

        # Retry on specific HTTP status codes (429, 500, 502, 503, 504)
        if isinstance(exception, requests.HTTPError):
            if exception.response is not None:
                status_code = exception.response.status_code
                # Rate limiting or server errors
                if status_code in [429, 500, 502, 503, 504]:
                    return True

        return False

    def _fetch_data(
        self,
        api_url: str,
        params: Optional[Dict[str, Any]] = None,
        to_pandas: bool = True,
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """
        Helper function to fetch data from the specified API URL with given parameters.
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
        :raises DTMApiAuthenticationError: If authentication fails.
        :raises DTMApiResponseError: If the API returns an error response.
        :raises DTMApiRequestError: If the request fails for other reasons.
        """
        logger.debug(f"Fetching data from {api_url} with params={params}")
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    # Exponential backoff: delay * (2 ^ (attempt - 1))
                    delay = self.retry_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying request (attempt {attempt + 1}/{self.max_retries + 1}) after {delay}s delay")
                    time.sleep(delay)

                response = requests.get(
                    api_url, params=params, headers=self._headers(), timeout=self.timeout
                )
                logger.debug(f"Received response: status={response.status_code}")
                response.raise_for_status()
                data = response.json()

                # For endpoints that wrap result in 'isSuccess'
                if not data.get("isSuccess"):
                    error_messages = data.get("errorMessages", [])
                    error_message = (
                        error_messages[0] if error_messages else "Unknown API error"
                    )
                    logger.error(f"API returned error: {error_message}")
                    raise DTMApiResponseError(error_message, error_messages)

                result = data["result"]
                result_count = len(result) if isinstance(result, list) else 1
                logger.info(f"Successfully fetched {result_count} records from {api_url}")
                return pd.DataFrame(result) if to_pandas else result

            except requests.Timeout as e:
                last_exception = e
                logger.warning(f"Request timed out after {self.timeout} seconds: {api_url}")
                if not self._is_retryable_error(e) or attempt >= self.max_retries:
                    logger.error(f"Request timed out after {self.timeout} seconds (no more retries)")
                    raise DTMApiTimeoutError(
                        f"Request timed out after {self.timeout} seconds"
                    ) from e
            except requests.HTTPError as e:
                last_exception = e
                if e.response.status_code == 401 or e.response.status_code == 403:
                    logger.error(f"Authentication failed: {e.response.status_code}")
                    raise DTMAuthenticationError(
                        f"Authentication failed: {e.response.status_code} {e.response.reason}"
                    ) from e
                logger.warning(f"HTTP error: {e.response.status_code} {e.response.reason}")
                if not self._is_retryable_error(e) or attempt >= self.max_retries:
                    logger.error(f"HTTP error occurred (no more retries): {e.response.status_code}")
                    raise DTMApiRequestError(
                        f"HTTP error occurred: {e.response.status_code} {e.response.reason}"
                    ) from e
            except requests.RequestException as e:
                last_exception = e
                logger.warning(f"Request failed: {e}")
                if not self._is_retryable_error(e) or attempt >= self.max_retries:
                    logger.error(f"Request failed (no more retries): {e}")
                    raise DTMApiRequestError(f"API request failed: {e}") from e

        # This should not be reached, but just in case
        if last_exception:
            raise DTMApiRequestError(f"API request failed after {self.max_retries} retries") from last_exception

    # ----------- Public API Methods -----------

    def get_all_countries(
        self, to_pandas: bool = True
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """
        Retrieve all countries for which DTM data is publicly available through the API.

        :return: All countries for which DTM data is publicly available through the API.
        :rtype: Union[pd.DataFrame, Dict[str, Any]]
        """
        return self._fetch_data(self._get_endpoint("countries"), to_pandas=to_pandas)

    def get_all_operations(
        self, to_pandas: bool = True
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """
        Retrieve all operations for which DTM data is publicly available through the API.

        :return: All operations for which DTM data is publicly available through the API.
        :rtype: Union[pd.DataFrame, Dict[str, Any]]
        """
        return self._fetch_data(self._get_endpoint("operations"), to_pandas=to_pandas)

    def get_idp_admin0_data(
        self,
        Operation: Optional[str] = None,
        CountryName: Optional[str] = None,
        Admin0Pcode: Optional[str] = None,
        FromReportingDate: Optional[str] = None,
        ToReportingDate: Optional[str] = None,
        FromRoundNumber: Optional[int] = None,
        ToRoundNumber: Optional[int] = None,
        to_pandas: bool = True,
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """
        Retrieve IDP data at Admin 0 level based on specified parameters.

        At least one of the following parameters must be provided:
        Operation, CountryName, or Admin0Pcode.

        :param Operation: Name of the DTM operation for which the data was collected.
        :type Operation: Optional[str]
        :param CountryName: Name of the country where the data was collected.
        :type CountryName: Optional[str]
        :param Admin0Pcode: Country code (ISO 3166-1 alpha-3).
        :type Admin0Pcode: Optional[str]
        :param FromReportingDate: Start date for the reporting period (format: 'YYYY-MM-DD').
        :type FromReportingDate: Optional[str]
        :param ToReportingDate: End date for the reporting period (format: 'YYYY-MM-DD').
        :type ToReportingDate: Optional[str]
        :param FromRoundNumber: Starting round number for the data collection range.
        :type FromRoundNumber: Optional[int]
        :param ToRoundNumber: Ending round number for the data collection range.
        :type ToRoundNumber: Optional[int]
        :param to_pandas: If True, the data will be returned as a pandas DataFrame. Otherwise, it will be returned as a JSON object.
        :type to_pandas: bool

        :return: The IDP Admin0 data matching the specified criteria, either as a DataFrame or a JSON object.
        :rtype: Union[pd.DataFrame, Dict[str, Any]]
        :raises ValidationError: If parameter validation fails.
        """
        # Validate required parameters
        validate_required_params(
            {"Operation": Operation, "CountryName": CountryName, "Admin0Pcode": Admin0Pcode},
            ["Operation", "CountryName", "Admin0Pcode"]
        )

        # Validate date formats
        if FromReportingDate:
            validate_date_format(FromReportingDate, "FromReportingDate")
        if ToReportingDate:
            validate_date_format(ToReportingDate, "ToReportingDate")
        validate_date_range(FromReportingDate, ToReportingDate, "FromReportingDate", "ToReportingDate")

        # Validate round numbers
        validate_round_number_range(FromRoundNumber, ToRoundNumber)

        params = {
            "Operation": Operation,
            "CountryName": CountryName,
            "Admin0Pcode": Admin0Pcode,
            "FromReportingDate": FromReportingDate,
            "ToReportingDate": ToReportingDate,
            "FromRoundNumber": FromRoundNumber,
            "ToRoundNumber": ToRoundNumber,
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        return self._fetch_data(self._get_endpoint("admin0"), params, to_pandas)

    def get_idp_admin1_data(
        self,
        Operation: Optional[str] = None,
        CountryName: Optional[str] = None,
        Admin0Pcode: Optional[str] = None,
        Admin1Name: Optional[str] = None,
        Admin1Pcode: Optional[str] = None,
        FromReportingDate: Optional[str] = None,
        ToReportingDate: Optional[str] = None,
        FromRoundNumber: Optional[int] = None,
        ToRoundNumber: Optional[int] = None,
        to_pandas: bool = True,
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """
        Retrieve IDP data at Admin 1 level based on specified parameters.

        At least one of the following parameters must be provided:
        Operation, CountryName, or Admin0Pcode.

        :param Operation: Name of the DTM operation for which the data was collected.
        :type Operation: Optional[str]
        :param CountryName: Name of the country where the data was collected.
        :type CountryName: Optional[str]
        :param Admin0Pcode: Country code (ISO 3166-1 alpha-3).
        :type Admin0Pcode: Optional[str]
        :param Admin1Name: Name of level 1 administrative boundaries.
        :type Admin1Name: Optional[str]
        :param Admin1Pcode: Place code of level 1 administrative boundaries.
        :type Admin1Pcode: Optional[str]
        :param FromReportingDate: Start date for the reporting period (format: 'YYYY-MM-DD').
        :type FromReportingDate: Optional[str]
        :param ToReportingDate: End date for the reporting period (format: 'YYYY-MM-DD').
        :type ToReportingDate: Optional[str]
        :param FromRoundNumber: Starting round number for the data collection range.
        :type FromRoundNumber: Optional[int]
        :param ToRoundNumber: Ending round number for the data collection range.
        :type ToRoundNumber: Optional[int]
        :param to_pandas: If True, the data will be returned as a pandas DataFrame. Otherwise, it will be returned as a JSON object.
        :type to_pandas: bool

        :return: The IDP Admin1 data matching the specified criteria, either as a DataFrame or a JSON object.
        :rtype: Union[pd.DataFrame, Dict[str, Any]]
        :raises ValidationError: If parameter validation fails.
        """
        # Validate required parameters
        validate_required_params(
            {"Operation": Operation, "CountryName": CountryName, "Admin0Pcode": Admin0Pcode},
            ["Operation", "CountryName", "Admin0Pcode"]
        )

        # Validate date formats
        if FromReportingDate:
            validate_date_format(FromReportingDate, "FromReportingDate")
        if ToReportingDate:
            validate_date_format(ToReportingDate, "ToReportingDate")
        validate_date_range(FromReportingDate, ToReportingDate, "FromReportingDate", "ToReportingDate")

        # Validate round numbers
        validate_round_number_range(FromRoundNumber, ToRoundNumber)

        params = {
            "Operation": Operation,
            "CountryName": CountryName,
            "Admin0Pcode": Admin0Pcode,
            "Admin1Name": Admin1Name,
            "Admin1Pcode": Admin1Pcode,
            "FromReportingDate": FromReportingDate,
            "ToReportingDate": ToReportingDate,
            "FromRoundNumber": FromRoundNumber,
            "ToRoundNumber": ToRoundNumber,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return self._fetch_data(self._get_endpoint("admin1"), params, to_pandas)

    def get_idp_admin2_data(
        self,
        Operation: Optional[str] = None,
        CountryName: Optional[str] = None,
        Admin0Pcode: Optional[str] = None,
        Admin1Name: Optional[str] = None,
        Admin1Pcode: Optional[str] = None,
        Admin2Name: Optional[str] = None,
        Admin2Pcode: Optional[str] = None,
        FromReportingDate: Optional[str] = None,
        ToReportingDate: Optional[str] = None,
        FromRoundNumber: Optional[int] = None,
        ToRoundNumber: Optional[int] = None,
        to_pandas: bool = True,
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """
        Retrieve IDP data at Admin 2 level based on specified parameters.

        At least one of the following parameters must be provided:
        Operation, CountryName, or Admin0Pcode.

        :param Operation: Name of the DTM operation for which the data was collected.
        :type Operation: Optional[str]
        :param CountryName: Name of the country where the data was collected.
        :type CountryName: Optional[str]
        :param Admin0Pcode: Country code (ISO 3166-1 alpha-3).
        :type Admin0Pcode: Optional[str]
        :param Admin1Name: Name of level 1 administrative boundaries.
        :type Admin1Name: Optional[str]
        :param Admin1Pcode: Place code of level 1 administrative boundaries.
        :type Admin1Pcode: Optional[str]
        :param Admin2Name: Name of level 2 administrative boundaries.
        :type Admin2Name: Optional[str]
        :param Admin2Pcode: Place code of level 2 administrative boundaries.
        :type Admin2Pcode: Optional[str]
        :param FromReportingDate: Start date for the reporting period (format: 'YYYY-MM-DD').
        :type FromReportingDate: Optional[str]
        :param ToReportingDate: End date for the reporting period (format: 'YYYY-MM-DD').
        :type ToReportingDate: Optional[str]
        :param FromRoundNumber: Starting round number for the data collection range.
        :type FromRoundNumber: Optional[int]
        :param ToRoundNumber: Ending round number for the data collection range.
        :type ToRoundNumber: Optional[int]
        :param to_pandas: If True, the data will be returned as a pandas DataFrame. Otherwise, it will be returned as a JSON object.
        :type to_pandas: bool

        :returns: The IDP Admin2 data matching the specified criteria, either as a DataFrame or a JSON object.
        :rtype: Union[pd.DataFrame, Dict[str, Any]]
        :raises ValidationError: If parameter validation fails.
        """
        # Validate required parameters
        validate_required_params(
            {"Operation": Operation, "CountryName": CountryName, "Admin0Pcode": Admin0Pcode},
            ["Operation", "CountryName", "Admin0Pcode"]
        )

        # Validate date formats
        if FromReportingDate:
            validate_date_format(FromReportingDate, "FromReportingDate")
        if ToReportingDate:
            validate_date_format(ToReportingDate, "ToReportingDate")
        validate_date_range(FromReportingDate, ToReportingDate, "FromReportingDate", "ToReportingDate")

        # Validate round numbers
        validate_round_number_range(FromRoundNumber, ToRoundNumber)

        params = {
            "Operation": Operation,
            "CountryName": CountryName,
            "Admin0Pcode": Admin0Pcode,
            "Admin1Name": Admin1Name,
            "Admin1Pcode": Admin1Pcode,
            "Admin2Name": Admin2Name,
            "Admin2Pcode": Admin2Pcode,
            "FromReportingDate": FromReportingDate,
            "ToReportingDate": ToReportingDate,
            "FromRoundNumber": FromRoundNumber,
            "ToRoundNumber": ToRoundNumber,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return self._fetch_data(self._get_endpoint("admin2"), params, to_pandas)
