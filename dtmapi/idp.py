import pandas as pd
import requests
from typing import Any, Dict, Optional, Union
from .config import IDP_ADMIN_0_API, IDP_ADMIN_1_API, IDP_ADMIN_2_API


def fetch_idp_data(
    api_url: str, params: Dict[str, Any], to_pandas: bool
) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Helper function to fetch IDP data from the specified API URL with given parameters.

    :param api_url: The API endpoint URL.
    :type api_url: str
    :param params: The query parameters for the API request.
    :type params: Dict[str, Any]
    :param to_pandas: If True, the data will be returned as a pandas DataFrame. Otherwise, it will be returned as a JSON object.
    :type to_pandas: bool
    :return: The IDP data matching the specified criteria, either as a DataFrame or a JSON object.
    :rtype: Union[pd.DataFrame, Dict[str, Any]]
    """
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data["isSuccess"]:
            if to_pandas:
                return pd.DataFrame(data["result"])
            else:
                return data["result"]
        else:
            raise ValueError(data["errorMessages"][0])
    except requests.RequestException as e:
        raise RuntimeError(f"API request failed: {e}")


def get_idp_admin0_data(
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
    Retrieve IDP Admin0 data based on specified parameters.

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
    return fetch_idp_data(IDP_ADMIN_0_API, params, to_pandas)


def get_idp_admin1_data(
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
    Retrieve IDP Admin1 data based on specified parameters.

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
    return fetch_idp_data(IDP_ADMIN_1_API, params, to_pandas)


def get_idp_admin2_data(
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
    Retrieve IDP Admin2 data based on specified parameters.

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

    :return: The IDP Admin2 data matching the specified criteria, either as a DataFrame or a JSON object.
    :rtype: Union[pd.DataFrame, Dict[str, Any]]
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
    return fetch_idp_data(IDP_ADMIN_2_API, params, to_pandas)
