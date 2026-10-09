import logging
from typing import Any, Dict, Optional, Union

import pandas as pd

from dtmapi._client import BaseDTMClient
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
from dtmapi.exceptions import DTMApiVersionError
from dtmapi.validators import (
    validate_date_format,
    validate_date_range,
    validate_required_params,
    validate_round_number_range,
)

# Configure logger
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class DTMApi(BaseDTMClient):
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

    For Humanitarian Needs Assessment data, see :class:`dtmapi.DTMHnaApi`.

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

    ENV_KEY_NAME = "DTMAPI_SUBSCRIPTION_KEY"

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
        # Validate API version before anything else, as in previous releases:
        # a bad version raises DTMApiVersionError even when no key is set.
        if api_version not in ["v2", "v3"]:
            raise DTMApiVersionError(
                f"api_version must be 'v2' or 'v3', got: '{api_version}'"
            )
        self.api_version = api_version

        super().__init__(
            subscription_key=subscription_key,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )

        self._logger.info(
            f"DTMApi client initialized with api_version={self.api_version}, "
            f"timeout={self.timeout}s, max_retries={self.max_retries}, "
            f"retry_delay={self.retry_delay}s"
        )

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
