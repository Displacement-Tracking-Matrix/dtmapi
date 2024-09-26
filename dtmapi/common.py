import pandas as pd
import requests

from typing import Any, Dict, Union
from .config import COUNTRY_LIST_API, OPERATION_LIST_API


def fetch_common_data(
    api_url: str, to_pandas: bool
) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Fetch common data from the specified API URL.

    :param api_url: The API endpoint URL.
    :type api_url: str
    :param to_pandas: If True, the data will be returned as a pandas DataFrame. Otherwise, it will be returned as a JSON object.
    :type to_pandas: bool
    :return: The data fetched from the API, either as a DataFrame or a JSON object.
    :rtype: Union[pd.DataFrame, Dict[str, Any]]
    """
    try:
        # Set headers (e.g., User-Agent) to mimic a browser request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

        # Send GET request to the API with headers
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx and 5xx)

        data = response.json()

        if to_pandas:
            return pd.DataFrame(data["result"])
        else:
            return data["result"]

    except requests.RequestException as e:
        raise RuntimeError(f"API request failed: {e}")


def get_all_countries(to_pandas: bool = True) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Retrieve all countries for which DTM data is publicly available through the API.

    :return: All countries for which DTM data is publicly available through the API.
    :rtype: Union[pd.DataFrame, Dict[str, Any]]
    """
    return fetch_common_data(COUNTRY_LIST_API, to_pandas)


def get_all_operations(to_pandas: bool = True) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Retrieve all operations for which DTM data is publicly available through the API.

    :return: All operations for which DTM data is publicly available through the API.
    :rtype: Union[pd.DataFrame, Dict[str, Any]]
    """
    return fetch_common_data(OPERATION_LIST_API, to_pandas)


# Example usage
if __name__ == "__main__":
    a = get_all_countries()
    print(a)