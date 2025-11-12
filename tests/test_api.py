"""Unit tests for DTMApi class."""

import os
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd
import requests

from dtmapi import (
    DTMApi,
    DTMApiRequestError,
    DTMApiResponseError,
    DTMApiTimeoutError,
    DTMAuthenticationError,
)


class TestDTMApiInit(unittest.TestCase):
    """Test DTMApi initialization."""

    def test_init_with_subscription_key(self):
        """Test initialization with a subscription key."""
        api = DTMApi(subscription_key="test-key")
        self.assertEqual(api.subscription_key, "test-key")
        self.assertEqual(api.timeout, 30)

    def test_init_with_custom_timeout(self):
        """Test initialization with custom timeout."""
        api = DTMApi(subscription_key="test-key", timeout=60)
        self.assertEqual(api.timeout, 60)

    @patch.dict(os.environ, {"DTMAPI_SUBSCRIPTION_KEY": "env-key"})
    def test_init_with_env_var(self):
        """Test initialization with environment variable."""
        api = DTMApi()
        self.assertEqual(api.subscription_key, "env-key")

    def test_init_without_key_raises_error(self):
        """Test that initialization without key raises DTMAuthenticationError."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(DTMAuthenticationError) as context:
                DTMApi()
            self.assertIn("Subscription Key is required", str(context.exception))


class TestDTMApiHeaders(unittest.TestCase):
    """Test DTMApi headers generation."""

    def test_headers(self):
        """Test that headers are correctly generated."""
        api = DTMApi(subscription_key="test-key")
        headers = api._headers()
        self.assertEqual(headers["Ocp-Apim-Subscription-Key"], "test-key")
        self.assertIn("User-Agent", headers)


class TestDTMApiFetchData(unittest.TestCase):
    """Test DTMApi _fetch_data method."""

    def setUp(self):
        """Set up test fixtures."""
        self.api = DTMApi(subscription_key="test-key")

    @patch("requests.get")
    def test_fetch_data_success_with_pandas(self, mock_get):
        """Test successful data fetch returning pandas DataFrame."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "isSuccess": True,
            "result": [{"country": "Ethiopia", "idps": 1000}],
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = self.api._fetch_data("http://test.com/api", to_pandas=True)

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["country"], "Ethiopia")
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_fetch_data_success_without_pandas(self, mock_get):
        """Test successful data fetch returning dict."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "isSuccess": True,
            "result": [{"country": "Ethiopia", "idps": 1000}],
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = self.api._fetch_data("http://test.com/api", to_pandas=False)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["country"], "Ethiopia")

    @patch("requests.get")
    def test_fetch_data_api_error(self, mock_get):
        """Test API error response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "isSuccess": False,
            "errorMessages": ["Invalid parameters"],
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with self.assertRaises(DTMApiResponseError) as context:
            self.api._fetch_data("http://test.com/api")
        self.assertEqual(str(context.exception), "Invalid parameters")
        self.assertEqual(context.exception.error_messages, ["Invalid parameters"])

    @patch("requests.get")
    def test_fetch_data_api_error_empty_messages(self, mock_get):
        """Test API error with empty error messages."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"isSuccess": False, "errorMessages": []}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with self.assertRaises(DTMApiResponseError) as context:
            self.api._fetch_data("http://test.com/api")
        self.assertEqual(str(context.exception), "Unknown API error")

    @patch("requests.get")
    def test_fetch_data_timeout(self, mock_get):
        """Test timeout error."""
        mock_get.side_effect = requests.Timeout("Connection timeout")

        with self.assertRaises(DTMApiTimeoutError) as context:
            self.api._fetch_data("http://test.com/api")
        self.assertIn("timed out after 30 seconds", str(context.exception))

    @patch("requests.get")
    def test_fetch_data_authentication_error_401(self, mock_get):
        """Test authentication error with 401 status."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.reason = "Unauthorized"
        http_error = requests.HTTPError()
        http_error.response = mock_response
        mock_get.side_effect = http_error

        with self.assertRaises(DTMAuthenticationError) as context:
            self.api._fetch_data("http://test.com/api")
        self.assertIn("401", str(context.exception))

    @patch("requests.get")
    def test_fetch_data_authentication_error_403(self, mock_get):
        """Test authentication error with 403 status."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.reason = "Forbidden"
        http_error = requests.HTTPError()
        http_error.response = mock_response
        mock_get.side_effect = http_error

        with self.assertRaises(DTMAuthenticationError) as context:
            self.api._fetch_data("http://test.com/api")
        self.assertIn("403", str(context.exception))

    @patch("requests.get")
    def test_fetch_data_http_error(self, mock_get):
        """Test HTTP error (non-auth)."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        http_error = requests.HTTPError()
        http_error.response = mock_response
        mock_get.side_effect = http_error

        with self.assertRaises(DTMApiRequestError) as context:
            self.api._fetch_data("http://test.com/api")
        self.assertIn("500", str(context.exception))

    @patch("requests.get")
    def test_fetch_data_request_error(self, mock_get):
        """Test general request error."""
        mock_get.side_effect = requests.ConnectionError("Network error")

        with self.assertRaises(DTMApiRequestError) as context:
            self.api._fetch_data("http://test.com/api")
        self.assertIn("API request failed", str(context.exception))

    @patch("requests.get")
    def test_fetch_data_with_timeout_parameter(self, mock_get):
        """Test that timeout parameter is passed to requests.get."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"isSuccess": True, "result": []}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        api = DTMApi(subscription_key="test-key", timeout=60)
        api._fetch_data("http://test.com/api")

        # Verify timeout was passed
        call_kwargs = mock_get.call_args[1]
        self.assertEqual(call_kwargs["timeout"], 60)


class TestDTMApiPublicMethods(unittest.TestCase):
    """Test DTMApi public methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.api = DTMApi(subscription_key="test-key")

    @patch("dtmapi.api.DTMApi._fetch_data")
    def test_get_all_countries(self, mock_fetch):
        """Test get_all_countries method."""
        mock_fetch.return_value = pd.DataFrame([{"country": "Ethiopia"}])
        result = self.api.get_all_countries()
        self.assertIsInstance(result, pd.DataFrame)
        mock_fetch.assert_called_once()

    @patch("dtmapi.api.DTMApi._fetch_data")
    def test_get_all_operations(self, mock_fetch):
        """Test get_all_operations method."""
        mock_fetch.return_value = pd.DataFrame([{"operation": "IDP Tracking"}])
        result = self.api.get_all_operations()
        self.assertIsInstance(result, pd.DataFrame)
        mock_fetch.assert_called_once()

    @patch("dtmapi.api.DTMApi._fetch_data")
    def test_get_idp_admin0_data(self, mock_fetch):
        """Test get_idp_admin0_data method."""
        mock_fetch.return_value = pd.DataFrame([{"country": "Ethiopia", "idps": 1000}])
        result = self.api.get_idp_admin0_data(CountryName="Ethiopia")
        self.assertIsInstance(result, pd.DataFrame)

        # Verify params were filtered correctly
        call_args = mock_fetch.call_args
        params = call_args[0][1]
        self.assertEqual(params["CountryName"], "Ethiopia")
        self.assertNotIn("Operation", params)

    @patch("dtmapi.api.DTMApi._fetch_data")
    def test_get_idp_admin1_data(self, mock_fetch):
        """Test get_idp_admin1_data method."""
        mock_fetch.return_value = pd.DataFrame([{"admin1": "Tigray", "idps": 500}])
        result = self.api.get_idp_admin1_data(
            CountryName="Ethiopia", Admin1Name="Tigray"
        )
        self.assertIsInstance(result, pd.DataFrame)

        # Verify params were filtered correctly
        call_args = mock_fetch.call_args
        params = call_args[0][1]
        self.assertEqual(params["CountryName"], "Ethiopia")
        self.assertEqual(params["Admin1Name"], "Tigray")

    @patch("dtmapi.api.DTMApi._fetch_data")
    def test_get_idp_admin2_data(self, mock_fetch):
        """Test get_idp_admin2_data method."""
        mock_fetch.return_value = pd.DataFrame([{"admin2": "District1", "idps": 200}])
        result = self.api.get_idp_admin2_data(
            CountryName="Ethiopia", Admin2Name="District1"
        )
        self.assertIsInstance(result, pd.DataFrame)

        # Verify params were filtered correctly
        call_args = mock_fetch.call_args
        params = call_args[0][1]
        self.assertEqual(params["CountryName"], "Ethiopia")
        self.assertEqual(params["Admin2Name"], "District1")

    @patch("dtmapi.api.DTMApi._fetch_data")
    def test_get_idp_admin0_data_filters_none_values(self, mock_fetch):
        """Test that None values are filtered from params."""
        mock_fetch.return_value = pd.DataFrame([])
        self.api.get_idp_admin0_data(
            CountryName="Ethiopia",
            Operation=None,
            FromRoundNumber=1,
            ToRoundNumber=None,
        )

        call_args = mock_fetch.call_args
        params = call_args[0][1]
        self.assertIn("CountryName", params)
        self.assertIn("FromRoundNumber", params)
        self.assertNotIn("Operation", params)
        self.assertNotIn("ToRoundNumber", params)


class TestDTMApiRetryLogic(unittest.TestCase):
    """Test DTMApi retry logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.api = DTMApi(subscription_key="test-key", max_retries=2, retry_delay=0.1)

    def test_init_with_retry_params(self):
        """Test initialization with retry parameters."""
        api = DTMApi(subscription_key="test-key", max_retries=5, retry_delay=2.0)
        self.assertEqual(api.max_retries, 5)
        self.assertEqual(api.retry_delay, 2.0)

    def test_init_default_retry_params(self):
        """Test default retry parameters."""
        api = DTMApi(subscription_key="test-key")
        self.assertEqual(api.max_retries, 3)
        self.assertEqual(api.retry_delay, 1)

    def test_is_retryable_error_timeout(self):
        """Test that timeout errors are retryable."""
        error = requests.Timeout("Connection timeout")
        self.assertTrue(self.api._is_retryable_error(error))

    def test_is_retryable_error_connection(self):
        """Test that connection errors are retryable."""
        error = requests.ConnectionError("Connection failed")
        self.assertTrue(self.api._is_retryable_error(error))

    def test_is_retryable_error_http_429(self):
        """Test that 429 errors are retryable."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        error = requests.HTTPError()
        error.response = mock_response
        self.assertTrue(self.api._is_retryable_error(error))

    def test_is_retryable_error_http_500(self):
        """Test that 500 errors are retryable."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        error = requests.HTTPError()
        error.response = mock_response
        self.assertTrue(self.api._is_retryable_error(error))

    def test_is_not_retryable_error_http_404(self):
        """Test that 404 errors are not retryable."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        error = requests.HTTPError()
        error.response = mock_response
        self.assertFalse(self.api._is_retryable_error(error))

    @patch("dtmapi.api.time.sleep")
    @patch("requests.get")
    def test_retry_on_timeout(self, mock_get, mock_sleep):
        """Test that request is retried on timeout."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"isSuccess": True, "result": []}
        mock_response.raise_for_status = MagicMock()

        mock_get.side_effect = [
            requests.Timeout("Timeout 1"),
            requests.Timeout("Timeout 2"),
            mock_response,
        ]

        result = self.api._fetch_data("http://test.com/api")

        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("dtmapi.api.time.sleep")
    @patch("requests.get")
    def test_retry_exhaustion(self, mock_get, mock_sleep):
        """Test that retries are exhausted and error is raised."""
        mock_get.side_effect = requests.Timeout("Persistent timeout")

        with self.assertRaises(DTMApiTimeoutError):
            self.api._fetch_data("http://test.com/api")

        self.assertEqual(mock_get.call_count, 3)

    @patch("requests.get")
    def test_no_retry_on_auth_error(self, mock_get):
        """Test that authentication errors are not retried."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.reason = "Unauthorized"
        error = requests.HTTPError()
        error.response = mock_response
        mock_get.side_effect = error

        with self.assertRaises(DTMAuthenticationError):
            self.api._fetch_data("http://test.com/api")

        self.assertEqual(mock_get.call_count, 1)


class TestDTMApiValidation(unittest.TestCase):
    """Test DTMApi parameter validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.api = DTMApi(subscription_key="test-key")

    def test_missing_required_params(self):
        """Test that missing required params raises ValidationError."""
        from dtmapi import ValidationError
        with self.assertRaises(ValidationError) as context:
            self.api.get_idp_admin0_data()
        self.assertIn("At least one", str(context.exception))

    def test_invalid_date_format(self):
        """Test that invalid date format raises ValidationError."""
        from dtmapi import ValidationError
        with self.assertRaises(ValidationError) as context:
            self.api.get_idp_admin0_data(
                CountryName="Ethiopia",
                FromReportingDate="01-01-2024"
            )
        self.assertIn("YYYY-MM-DD", str(context.exception))

    def test_invalid_date_range(self):
        """Test that invalid date range raises ValidationError."""
        from dtmapi import ValidationError
        with self.assertRaises(ValidationError) as context:
            self.api.get_idp_admin0_data(
                CountryName="Ethiopia",
                FromReportingDate="2024-12-31",
                ToReportingDate="2024-01-01"
            )
        self.assertIn("must be before or equal to", str(context.exception))

    def test_invalid_round_number(self):
        """Test that invalid round number raises ValidationError."""
        from dtmapi import ValidationError
        with self.assertRaises(ValidationError) as context:
            self.api.get_idp_admin0_data(
                CountryName="Ethiopia",
                FromRoundNumber=-1
            )
        self.assertIn("must be >= 1", str(context.exception))

    def test_invalid_round_range(self):
        """Test that invalid round range raises ValidationError."""
        from dtmapi import ValidationError
        with self.assertRaises(ValidationError) as context:
            self.api.get_idp_admin0_data(
                CountryName="Ethiopia",
                FromRoundNumber=10,
                ToRoundNumber=1
            )
        self.assertIn("must be <=", str(context.exception))

    @patch("dtmapi.api.DTMApi._fetch_data")
    def test_valid_params_pass_validation(self, mock_fetch):
        """Test that valid params pass validation."""
        mock_fetch.return_value = pd.DataFrame([])

        self.api.get_idp_admin0_data(
            CountryName="Ethiopia",
            FromReportingDate="2024-01-01",
            ToReportingDate="2024-12-31",
            FromRoundNumber=1,
            ToRoundNumber=10
        )

        mock_fetch.assert_called_once()


class TestDTMApiVersions(unittest.TestCase):
    """Test DTMApi version selection and endpoint routing."""

    def test_init_with_v3_version(self):
        """Test initialization with v3 version."""
        api = DTMApi(subscription_key="test-key", api_version="v3")
        self.assertEqual(api.api_version, "v3")

    def test_init_with_v2_version(self):
        """Test initialization with v2 version."""
        api = DTMApi(subscription_key="test-key", api_version="v2")
        self.assertEqual(api.api_version, "v2")

    def test_init_default_version_is_v3(self):
        """Test that default version is v3."""
        api = DTMApi(subscription_key="test-key")
        self.assertEqual(api.api_version, "v3")

    def test_init_invalid_version_raises_error(self):
        """Test that invalid version raises DTMApiVersionError."""
        from dtmapi import DTMApiVersionError
        with self.assertRaises(DTMApiVersionError) as context:
            DTMApi(subscription_key="test-key", api_version="v1")
        self.assertIn("must be 'v2' or 'v3'", str(context.exception))

    def test_get_endpoint_v3_admin0(self):
        """Test endpoint selection for v3 admin0."""
        api = DTMApi(subscription_key="test-key", api_version="v3")
        endpoint = api._get_endpoint("admin0")
        self.assertIn("/v3/displacement/admin0", endpoint)

    def test_get_endpoint_v2_admin0(self):
        """Test endpoint selection for v2 admin0."""
        api = DTMApi(subscription_key="test-key", api_version="v2")
        endpoint = api._get_endpoint("admin0")
        self.assertIn("/v2/IdpAdmin0Data", endpoint)

    def test_get_endpoint_v3_admin1(self):
        """Test endpoint selection for v3 admin1."""
        api = DTMApi(subscription_key="test-key", api_version="v3")
        endpoint = api._get_endpoint("admin1")
        self.assertIn("/v3/displacement/admin1", endpoint)

    def test_get_endpoint_v2_admin1(self):
        """Test endpoint selection for v2 admin1."""
        api = DTMApi(subscription_key="test-key", api_version="v2")
        endpoint = api._get_endpoint("admin1")
        self.assertIn("/v2/IdpAdmin1Data", endpoint)

    def test_get_endpoint_v3_admin2(self):
        """Test endpoint selection for v3 admin2."""
        api = DTMApi(subscription_key="test-key", api_version="v3")
        endpoint = api._get_endpoint("admin2")
        self.assertIn("/v3/displacement/admin2", endpoint)

    def test_get_endpoint_v2_admin2(self):
        """Test endpoint selection for v2 admin2."""
        api = DTMApi(subscription_key="test-key", api_version="v2")
        endpoint = api._get_endpoint("admin2")
        self.assertIn("/v2/IdpAdmin2Data", endpoint)

    def test_get_endpoint_v3_countries(self):
        """Test endpoint selection for v3 countries."""
        api = DTMApi(subscription_key="test-key", api_version="v3")
        endpoint = api._get_endpoint("countries")
        self.assertIn("/v3/displacement/country-list", endpoint)

    def test_get_endpoint_v2_countries(self):
        """Test endpoint selection for v2 countries."""
        api = DTMApi(subscription_key="test-key", api_version="v2")
        endpoint = api._get_endpoint("countries")
        self.assertIn("/v2/CountryList", endpoint)

    def test_get_endpoint_v3_operations(self):
        """Test endpoint selection for v3 operations."""
        api = DTMApi(subscription_key="test-key", api_version="v3")
        endpoint = api._get_endpoint("operations")
        self.assertIn("/v3/displacement/operation-list", endpoint)

    def test_get_endpoint_v2_operations(self):
        """Test endpoint selection for v2 operations."""
        api = DTMApi(subscription_key="test-key", api_version="v2")
        endpoint = api._get_endpoint("operations")
        self.assertIn("/v2/OperationList", endpoint)

    @patch("dtmapi.api.DTMApi._fetch_data")
    def test_v2_idp_admin0_uses_correct_endpoint(self, mock_fetch):
        """Test that v2 get_idp_admin0_data uses v2 endpoint."""
        mock_fetch.return_value = pd.DataFrame([])
        api = DTMApi(subscription_key="test-key", api_version="v2")
        api.get_idp_admin0_data(CountryName="Ethiopia")

        # Verify the endpoint URL contains v2
        call_args = mock_fetch.call_args
        endpoint_url = call_args[0][0]
        self.assertIn("/v2/IdpAdmin0Data", endpoint_url)

    @patch("dtmapi.api.DTMApi._fetch_data")
    def test_v3_idp_admin0_uses_correct_endpoint(self, mock_fetch):
        """Test that v3 get_idp_admin0_data uses v3 endpoint."""
        mock_fetch.return_value = pd.DataFrame([])
        api = DTMApi(subscription_key="test-key", api_version="v3")
        api.get_idp_admin0_data(CountryName="Ethiopia")

        # Verify the endpoint URL contains v3
        call_args = mock_fetch.call_args
        endpoint_url = call_args[0][0]
        self.assertIn("/v3/displacement/admin0", endpoint_url)

    @patch("dtmapi.api.DTMApi._fetch_data")
    def test_v2_countries_uses_correct_endpoint(self, mock_fetch):
        """Test that v2 get_all_countries uses v2 endpoint."""
        mock_fetch.return_value = pd.DataFrame([])
        api = DTMApi(subscription_key="test-key", api_version="v2")
        api.get_all_countries()

        # Verify the endpoint URL contains v2
        call_args = mock_fetch.call_args
        endpoint_url = call_args[0][0]
        self.assertIn("/v2/CountryList", endpoint_url)

    @patch("dtmapi.api.DTMApi._fetch_data")
    def test_v3_operations_uses_correct_endpoint(self, mock_fetch):
        """Test that v3 get_all_operations uses v3 endpoint."""
        mock_fetch.return_value = pd.DataFrame([])
        api = DTMApi(subscription_key="test-key", api_version="v3")
        api.get_all_operations()

        # Verify the endpoint URL contains v3
        call_args = mock_fetch.call_args
        endpoint_url = call_args[0][0]
        self.assertIn("/v3/displacement/operation-list", endpoint_url)


if __name__ == "__main__":
    unittest.main()
