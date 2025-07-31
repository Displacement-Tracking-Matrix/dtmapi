import os
from typing import Any, Dict, Optional, Union

import pandas as pd
import requests

from dtmapi.config import (
    COUNTRY_LIST_API,
    IDP_ADMIN_0_API,
    IDP_ADMIN_1_API,
    IDP_ADMIN_2_API,
    OPERATION_LIST_API,
)


class DTMApi:
    """
    Python interface to DTM API v3 endpoints. Requires Ocp-Apim-Subscription-Key.
    """

    def __init__(self, subscription_key: Optional[str] = None):
        """
        Initialize the client with a subscription key. Key can be passed directly,
        or set as the DTMAPI_SUBSCRIPTION_KEY environment variable.
        """
        self.subscription_key = subscription_key or os.getenv("DTMAPI_SUBSCRIPTION_KEY")
        if not self.subscription_key:
            raise ValueError(
                "A DTM API Subscription Key is required. "
                "Provide it as an argument or set the DTMAPI_SUBSCRIPTION_KEY environment variable."
            )

    def _headers(self) -> Dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (compatible; DTMClient/2.0)",
            "Ocp-Apim-Subscription-Key": self.subscription_key,
        }

    def _fetch_data(
        self,
        api_url: str,
        params: Optional[Dict[str, Any]] = None,
        to_pandas: bool = True,
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """
        Helper function to fetch data from the specified API URL with given parameters.

        :param api_url: The API endpoint URL.
        :type api_url: str
        :param params: The query parameters for the API request.
        :type params: Dict[str, Any]
        :param to_pandas: If True, the data will be returned as a pandas DataFrame. Otherwise, it will be returned as a JSON object.
        :type to_pandas: bool
        :return: The data matching the specified criteria, either as a DataFrame or a JSON object.
        :rtype: Union[pd.DataFrame, Dict[str, Any]]
        """
        try:
            response = requests.get(api_url, params=params, headers=self._headers())
            response.raise_for_status()
            data = response.json()

            # For endpoints that wrap result in 'isSuccess'
            if not data.get("isSuccess"):
                raise ValueError(data.get("errorMessages", ["Unknown error"])[0])
            result = data["result"]

            return pd.DataFrame(result) if to_pandas else result

        except requests.RequestException as e:
            raise RuntimeError(f"API request failed: {e}")

    # ----------- Public API Methods -----------

    def get_all_countries(
        self, to_pandas: bool = True
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """
        Retrieve all countries for which DTM data is publicly available through the API.

        :return: All countries for which DTM data is publicly available through the API.
        :rtype: Union[pd.DataFrame, Dict[str, Any]]
        """
        return self._fetch_data(COUNTRY_LIST_API, to_pandas=to_pandas)

    def get_all_operations(
        self, to_pandas: bool = True
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """
        Retrieve all operations for which DTM data is publicly available through the API.

        :return: All operations for which DTM data is publicly available through the API.
        :rtype: Union[pd.DataFrame, Dict[str, Any]]
        """
        return self._fetch_data(OPERATION_LIST_API, to_pandas=to_pandas)

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
        """
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
        return self._fetch_data(IDP_ADMIN_0_API, params, to_pandas)

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
        """
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
        return self._fetch_data(IDP_ADMIN_1_API, params, to_pandas)

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
                If ``to_pandas`` is True, the DataFrame includes the following columns:
                    - **id** (*int*): Unique identifier for the record.
                    - **operation** (*str*): Name of DTM Operation for which the data was collected.
                    - **admin0Name** (*str*): Country name.
                    - **admin0Pcode** (*str*): Country code (ISO 3166-1 alpha-3).
                    - **admin1Name** (*str*): Name of level 1 administrative boundaries.
                    - **admin1Pcode** (*str*): Place code of level 1 administrative boundaries.
                    - **admin2Name** (*str*): Name of level 2 administrative boundaries.
                    - **admin2Pcode** (*str*): Place code of level 2 administrative boundaries.
                    - **numPresentIdpInd** (*int*): Number of IDPs at Admin level.
                    - **reportingDate** (*str*): Data reporting date/snapshot date.
                    - **yearReportingDate** (*int*): Year of reporting/ snapshot date.
                    - **monthReportingDate** (*int*): Month of reporting/ snapshot date.
                    - **roundNumber** (*int*): Data collection round number.
                    - **assessmentType** (*str*): Type of the assessment

        :rtype: Union[pd.DataFrame, Dict[str, Any]]

        :raises ValueError: If the API response indicates an error.
        :raises RuntimeError: If there is a network or request failure.
        """
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
        return self._fetch_data(IDP_ADMIN_2_API, params, to_pandas)
