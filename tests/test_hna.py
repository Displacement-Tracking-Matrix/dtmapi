"""
Tests for the HNA client and for the shared base extracted in 0.2.0.

No network access and no subscription key required: every request is stubbed.
Note the patch target is ``dtmapi._client.requests.get`` -- requests now lives
in the shared base rather than in ``dtmapi.api``.
"""
import json
import pathlib
import tempfile
import unittest
from unittest import mock

import pandas as pd
import requests

import dtmapi
from dtmapi import DTMApi, DTMHnaApi
from dtmapi.exceptions import DTMApiError, DTMApiVersionError, DTMAuthenticationError, DTMApiResponseError
from dtmapi.hna.exceptions import (
    HNAAuthError,
    HNARequestError,
    HNAError,
    HNAResponseError,
    HNATimeoutError,
    HNAVersionError,
)
from dtmapi.validators import ValidationError

KEY = "test-idp-key-123"
HNA_KEY = "test-hna-key-456"


def fake_response(payload, status=200):
    r = requests.Response()
    r.status_code = status
    r._content = json.dumps(payload).encode()
    r.url = "http://test"
    return r


ENVELOPE = {"isSuccess": True, "result": [{"admin0Name": "Ethiopia", "numPresentIdpInd": 42}]}


def hna_response(rows, page=1, page_size=100, total=None):
    """The real shape of an HNA admin2 response: result -> result -> data."""
    total = len(rows) if total is None else total
    total_pages = max(1, -(-total // page_size))
    return fake_response({
        "result": {
            "result": {
                "data": rows,
                "pagination": {
                    "page": page,
                    "pageSize": page_size,
                    "totalItems": total,
                    "totalPages": total_pages,
                    "hasNextPage": page < total_pages,
                    "hasPreviousPage": page > 1,
                },
            },
            "statusCode": 200,
            "isSuccess": True,
            "errorMessages": [],
            "totalRecordsCount": len(rows),
        },
        "id": 103,
        "exception": None,
        "status": 5,
        "isCompletedSuccessfully": True,
    })
BARE_LIST = [{"admin0Name": "Ethiopia", "pin": 42}]


class TestPublicSurface(unittest.TestCase):
    def test_both_clients_exported(self):
        self.assertIn("DTMApi", dtmapi.__all__)
        self.assertIn("DTMHnaApi", dtmapi.__all__)
        self.assertIs(dtmapi.DTMHnaApi, DTMHnaApi)

    def test_dtmapi_signature_unchanged(self):
        api = DTMApi(subscription_key=KEY)
        self.assertEqual(api.api_version, "v3")
        self.assertEqual(api.timeout, 30)
        self.assertEqual(api.max_retries, 3)
        self.assertEqual(api.retry_delay, 1)
        for name in ("get_all_countries", "get_all_operations",
                     "get_idp_admin0_data", "get_idp_admin1_data", "get_idp_admin2_data"):
            self.assertTrue(callable(getattr(api, name)), name)

    def test_version_validated_before_key(self):
        # Previous behaviour: a bad version raises even with no key present.
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(DTMApiVersionError):
                DTMApi(api_version="v9")

    def test_missing_key_raises(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(DTMAuthenticationError) as ctx:
                DTMApi()
            self.assertIn("DTMAPI_SUBSCRIPTION_KEY", str(ctx.exception))

    def test_env_var_still_works(self):
        with mock.patch.dict("os.environ", {"DTMAPI_SUBSCRIPTION_KEY": KEY}, clear=True):
            self.assertEqual(DTMApi().subscription_key, KEY)

    def test_repr_masks_key(self):
        self.assertNotIn(KEY, repr(DTMApi(subscription_key=KEY)))


class TestSharedPlumbing(unittest.TestCase):
    def test_header_shape_shared_key_is_not(self):
        idp = DTMApi(subscription_key=KEY)._headers()
        hna = DTMHnaApi(subscription_key=HNA_KEY)._headers()
        self.assertEqual(sorted(idp), sorted(hna))
        self.assertNotEqual(
            idp["Ocp-Apim-Subscription-Key"], hna["Ocp-Apim-Subscription-Key"]
        )

    @mock.patch("dtmapi._client.requests.get")
    def test_idp_fetch_returns_dataframe(self, get):
        get.return_value = fake_response(ENVELOPE)
        df = DTMApi(subscription_key=KEY).get_idp_admin0_data(CountryName="Ethiopia")
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(df.iloc[0]["admin0Name"], "Ethiopia")
        sent = get.call_args.kwargs["params"]
        self.assertEqual(sent, {"CountryName": "Ethiopia"})  # None values dropped

    @mock.patch("dtmapi._client.requests.get")
    def test_to_pandas_false(self, get):
        get.return_value = fake_response(ENVELOPE)
        raw = DTMApi(subscription_key=KEY).get_all_countries(to_pandas=False)
        self.assertIsInstance(raw, list)

    @mock.patch("dtmapi._client.requests.get")
    def test_api_error_envelope(self, get):
        get.return_value = fake_response({"isSuccess": False, "errorMessages": ["bad country"]})
        with self.assertRaises(DTMApiResponseError) as ctx:
            DTMApi(subscription_key=KEY).get_idp_admin0_data(CountryName="Nowhere")
        self.assertIn("bad country", str(ctx.exception))

    @mock.patch("dtmapi._client.time.sleep")
    @mock.patch("dtmapi._client.requests.get")
    def test_retry_then_success(self, get, sleep):
        get.side_effect = [requests.ConnectionError("boom"), fake_response(ENVELOPE)]
        df = DTMApi(subscription_key=KEY).get_all_countries()
        self.assertEqual(len(df), 1)
        self.assertEqual(get.call_count, 2)
        self.assertEqual(sleep.call_count, 1)

    @mock.patch("dtmapi._client.requests.get")
    def test_auth_error_not_retried(self, get):
        resp = fake_response({}, status=401)
        get.side_effect = requests.HTTPError(response=resp)
        with self.assertRaises(DTMAuthenticationError):
            DTMApi(subscription_key=KEY).get_all_countries()
        self.assertEqual(get.call_count, 1)

    def test_validation_still_enforced(self):
        api = DTMApi(subscription_key=KEY)
        with self.assertRaises(ValidationError):
            api.get_idp_admin0_data()  # none of the required three
        with self.assertRaises(ValidationError):
            api.get_idp_admin0_data(CountryName="Chad", FromReportingDate="01-01-2020")


class TestHna(unittest.TestCase):
    def test_defaults(self):
        hna = DTMHnaApi(subscription_key=KEY)
        self.assertEqual(hna.api_version, "v1")
        self.assertEqual(hna.environment, "dev")

    def test_bad_version(self):
        with self.assertRaises(HNAVersionError):
            DTMHnaApi(subscription_key=KEY, api_version="v3")

    def test_bad_environment(self):
        with self.assertRaises(HNAVersionError):
            DTMHnaApi(subscription_key=KEY, environment="staging")

    def test_reads_its_own_env_var(self):
        with mock.patch.dict("os.environ", {"DTMHNA_SUBSCRIPTION_KEY": HNA_KEY}, clear=True):
            self.assertEqual(DTMHnaApi().subscription_key, HNA_KEY)

    def test_never_falls_back_to_the_displacement_key(self):
        with mock.patch.dict("os.environ", {"DTMAPI_SUBSCRIPTION_KEY": KEY}, clear=True):
            with self.assertRaises(HNAAuthError) as ctx:
                DTMHnaApi()
            self.assertIn("DTMHNA_SUBSCRIPTION_KEY", str(ctx.exception))

    def test_two_clients_hold_distinct_keys(self):
        idp = DTMApi(subscription_key=KEY)
        hna = DTMHnaApi(subscription_key=HNA_KEY)
        self.assertEqual(idp._headers()["Ocp-Apim-Subscription-Key"], KEY)
        self.assertEqual(hna._headers()["Ocp-Apim-Subscription-Key"], HNA_KEY)

    @mock.patch("dtmapi._client.requests.get")
    def test_401_names_the_hna_service(self, get):
        get.side_effect = requests.HTTPError(response=fake_response({}, status=401))
        with self.assertRaises(HNAAuthError) as ctx:
            DTMHnaApi(subscription_key=KEY).get_all_countries()
        msg = str(ctx.exception)
        self.assertIn("Authentication failed: 401", msg)
        self.assertIn("DTM HNA API", msg)
        self.assertIn("DTMHNA_SUBSCRIPTION_KEY", msg)

    @mock.patch("dtmapi._client.requests.get")
    def test_hna_auth_error_still_caught_by_old_handler(self, get):
        get.side_effect = requests.HTTPError(response=fake_response({}, status=403))
        with self.assertRaises(DTMAuthenticationError):
            DTMHnaApi(subscription_key=KEY).get_all_countries()

    def test_environments_use_different_hosts(self):
        dev = DTMHnaApi(subscription_key=KEY, environment="dev")._get_endpoint("admin2")
        self.assertIn("dtm-apim-dev.iom.int", dev)
        self.assertTrue(dev.endswith("/HNA/v1/admin2"))

    def test_surface_matches_the_four_hna_endpoints(self):
        hna = DTMHnaApi(subscription_key=HNA_KEY)
        for name in ("get_all_countries", "get_hna_data_catalog",
                     "get_hna_admin2_data", "get_all_hna_admin2_data",
                     "download_hna_data"):
            self.assertTrue(callable(getattr(hna, name)), name)
        for name in ("get_hna_admin0_data", "get_hna_admin1_data"):
            self.assertFalse(hasattr(hna, name), f"{name} should be gone")

    # --- parameterless endpoints ---

    @mock.patch("dtmapi._client.requests.get")
    def test_countries_and_catalog_send_no_params(self, get):
        get.return_value = fake_response(BARE_LIST)
        hna = DTMHnaApi(subscription_key=HNA_KEY)
        hna.get_all_countries()
        self.assertIn("CountryList", get.call_args.args[0])
        self.assertIsNone(get.call_args.kwargs["params"])
        hna.get_hna_data_catalog()
        self.assertIn("HNADataCatalog", get.call_args.args[0])
        self.assertIsNone(get.call_args.kwargs["params"])

    # --- admin2 required parameters ---

    def test_admin0pcode_is_required(self):
        with self.assertRaises(ValidationError) as ctx:
            DTMHnaApi(subscription_key=HNA_KEY).get_hna_admin2_data(Year=2024)
        self.assertIn("Admin0Pcode", str(ctx.exception))

    def test_year_is_required(self):
        with self.assertRaises(ValidationError) as ctx:
            DTMHnaApi(subscription_key=HNA_KEY).get_hna_admin2_data(Admin0Pcode="ETH")
        self.assertIn("Year", str(ctx.exception))

    def test_year_must_be_an_integer(self):
        with self.assertRaises(ValidationError):
            DTMHnaApi(subscription_key=HNA_KEY).get_hna_admin2_data(
                Admin0Pcode="ETH", Year="not-a-year"
            )

    @mock.patch("dtmapi._client.requests.get")
    def test_year_coerced_to_int(self, get):
        get.return_value = fake_response(BARE_LIST)
        DTMHnaApi(subscription_key=HNA_KEY).get_hna_admin2_data(Admin0Pcode="ETH", Year="2024")
        self.assertEqual(get.call_args.kwargs["params"]["Year"], 2024)

    @mock.patch("dtmapi._client.requests.get")
    def test_admin2_sends_the_documented_params(self, get):
        get.return_value = fake_response(BARE_LIST)
        DTMHnaApi(subscription_key=HNA_KEY).get_hna_admin2_data(
            Admin0Pcode="ETH", Year=2024, Admin0Name="Ethiopia", PopulationGroup="IDP", Page=2
        )
        self.assertEqual(
            get.call_args.kwargs["params"],
            {"Admin0Pcode": "ETH", "Year": 2024, "Admin0Name": "Ethiopia",
             "PopulationGroup": "IDP", "Page": 2},
        )

    @mock.patch("dtmapi._client.requests.get")
    def test_optional_params_omitted_when_absent(self, get):
        get.return_value = fake_response(BARE_LIST)
        DTMHnaApi(subscription_key=HNA_KEY).get_hna_admin2_data(Admin0Pcode="ETH", Year=2024)
        self.assertEqual(
            get.call_args.kwargs["params"], {"Admin0Pcode": "ETH", "Year": 2024, "Page": 1}
        )

    # --- PopulationGroup normalisation ---

    @mock.patch("dtmapi._client.requests.get")
    def test_population_group_list_becomes_comma_string(self, get):
        get.return_value = fake_response(BARE_LIST)
        DTMHnaApi(subscription_key=HNA_KEY).get_hna_admin2_data(
            Admin0Pcode="ETH", Year=2024, PopulationGroup=["IDP", "Returnee"]
        )
        self.assertEqual(get.call_args.kwargs["params"]["PopulationGroup"], "IDP,Returnee")

    @mock.patch("dtmapi._client.requests.get")
    def test_population_group_string_passes_through(self, get):
        get.return_value = fake_response(BARE_LIST)
        DTMHnaApi(subscription_key=HNA_KEY).get_hna_admin2_data(
            Admin0Pcode="ETH", Year=2024, PopulationGroup="IDP, Returnee"
        )
        self.assertEqual(get.call_args.kwargs["params"]["PopulationGroup"], "IDP,Returnee")

    def test_empty_population_group_rejected(self):
        with self.assertRaises(ValidationError):
            DTMHnaApi(subscription_key=HNA_KEY).get_hna_admin2_data(
                Admin0Pcode="ETH", Year=2024, PopulationGroup="  "
            )

    # --- pagination ---

    @mock.patch("dtmapi._client.requests.get")
    def test_unwraps_the_double_envelope(self, get):
        # result -> result -> data, as the live API actually answers.
        get.return_value = hna_response(
            [{"m0302_meta_adm0_pcode": "NGA", "year": 2022, "num_households": 180}]
        )
        df = DTMHnaApi(subscription_key=HNA_KEY).get_hna_admin2_data(
            Admin0Pcode="NGA", Year=2022
        )
        self.assertEqual(list(df.columns), ["m0302_meta_adm0_pcode", "year", "num_households"])
        self.assertEqual(df.iloc[0]["num_households"], 180)

    @mock.patch("dtmapi._client.requests.get")
    def test_get_all_follows_hasnextpage(self, get):
        page1 = [{"n": i} for i in range(100)]
        page2 = [{"n": i} for i in range(17)]
        get.side_effect = [
            hna_response(page1, page=1, total=117),
            hna_response(page2, page=2, total=117),
        ]
        df = DTMHnaApi(subscription_key=HNA_KEY).get_all_hna_admin2_data(
            Admin0Pcode="NGA", Year=2022
        )
        self.assertEqual(len(df), 117)
        self.assertEqual(get.call_count, 2)  # stops without a wasted third call
        self.assertEqual([c.kwargs["params"]["Page"] for c in get.call_args_list], [1, 2])

    @mock.patch("dtmapi._client.requests.get")
    def test_get_all_stops_on_empty_page_without_pagination(self, get):
        get.side_effect = [
            fake_response([{"n": 1}, {"n": 2}]),
            fake_response([{"n": 3}]),
            fake_response([]),
        ]
        df = DTMHnaApi(subscription_key=HNA_KEY).get_all_hna_admin2_data(
            Admin0Pcode="ETH", Year=2024
        )
        self.assertEqual(len(df), 3)
        self.assertEqual(get.call_count, 3)

    @mock.patch("dtmapi._client.requests.get")
    def test_get_all_respects_max_pages(self, get):
        get.return_value = hna_response([{"n": 1}], page=1, total=10_000)
        df = DTMHnaApi(subscription_key=HNA_KEY).get_all_hna_admin2_data(
            Admin0Pcode="ETH", Year=2024, max_pages=3
        )
        self.assertEqual(get.call_count, 3)
        self.assertEqual(len(df), 3)

    @mock.patch("dtmapi._client.requests.get")
    def test_envelope_failure_raises_with_message(self, get):
        get.return_value = fake_response({
            "result": {"isSuccess": False, "errorMessages": ["Year is required"]},
            "exception": None,
        })
        with self.assertRaises(HNAResponseError) as ctx:
            DTMHnaApi(subscription_key=HNA_KEY).get_hna_admin2_data(Admin0Pcode="NGA", Year=2022)
        self.assertIn("Year is required", str(ctx.exception))

    @mock.patch("dtmapi._client.requests.get")
    def test_task_exception_raises(self, get):
        get.return_value = fake_response({"result": None, "exception": "Timeout in backend"})
        with self.assertRaises(HNAResponseError) as ctx:
            DTMHnaApi(subscription_key=HNA_KEY).get_all_countries()
        self.assertIn("Timeout in backend", str(ctx.exception))

    @mock.patch("dtmapi._client.requests.get")
    def test_data_must_be_a_list(self, get):
        get.return_value = fake_response({"result": {"data": {"oops": 1}}})
        with self.assertRaises(HNAResponseError):
            DTMHnaApi(subscription_key=HNA_KEY).get_all_countries()

    # --- download ---

    DOWNLOAD_INFO = {
        "downloadUrl": "https://gvamisssawe001.blob.core.windows.net/hna-api-temp-files/"
                       "608a4e90-5085-4e39-8694-4d37133bc19c/Report_NGA_2022__20260914101710.xlsx",
        "fileName": "Report_NGA_2022__20260914101710.xlsx",
        "expiresAt": "2026-09-14T10:27:10.6753967+00:00",
    }

    def _routed_get(self, blob_content=b"PK\x03\x04 fake xlsx", blob_error=None):
        """
        One mock for both hops.

        dtmapi.hna.api.requests and dtmapi._client.requests are the same module
        object, so they cannot be patched separately. Dispatching on the URL is
        also closer to what actually happens.
        """
        calls = []

        def side_effect(url, **kwargs):
            calls.append((url, kwargs))
            if "blob.core.windows.net" in url:
                if blob_error is not None:
                    raise blob_error
                r = requests.Response()
                r.status_code = 200
                r._content = blob_content
                return r
            return fake_response(self.DOWNLOAD_INFO)

        return side_effect, calls

    @mock.patch("dtmapi._client.requests.get")
    def test_download_url_returns_the_pointer(self, get):
        get.return_value = fake_response(self.DOWNLOAD_INFO)
        info = DTMHnaApi(subscription_key=HNA_KEY).get_hna_download_url(
            Admin0Pcode="NGA", Year=2022
        )
        self.assertEqual(info["fileName"], "Report_NGA_2022__20260914101710.xlsx")
        self.assertIn("blob.core.windows.net", info["downloadUrl"])
        # .NET writes 7 fractional digits; fromisoformat accepts 6.
        self.assertEqual(info["expires_at"].year, 2026)
        self.assertEqual(info["expires_at"].minute, 27)

    @mock.patch("dtmapi._client.requests.get")
    def test_download_follows_the_blob_link(self, get):
        get.side_effect, calls = self._routed_get()
        out = DTMHnaApi(subscription_key=HNA_KEY).download_hna_data(
            Admin0Pcode="NGA", Year=2022
        )
        self.assertEqual(out, b"PK\x03\x04 fake xlsx")
        self.assertEqual(len(calls), 2)

        api_url, api_kwargs = calls[0]
        self.assertIn("/download", api_url)
        self.assertEqual(api_kwargs["headers"]["Ocp-Apim-Subscription-Key"], HNA_KEY)

        blob_url, blob_kwargs = calls[1]
        self.assertEqual(blob_url, self.DOWNLOAD_INFO["downloadUrl"])
        # Different host: the subscription key must not travel with it.
        self.assertNotIn("headers", blob_kwargs)

    @mock.patch("dtmapi._client.requests.get")
    def test_download_to_directory_uses_the_api_filename(self, get):
        get.side_effect, _ = self._routed_get(blob_content=b"payload")
        with tempfile.TemporaryDirectory() as tmp:
            out = DTMHnaApi(subscription_key=HNA_KEY).download_hna_data(
                Admin0Pcode="NGA", Year=2022, file_path=tmp
            )
            self.assertEqual(out.name, "Report_NGA_2022__20260914101710.xlsx")
            self.assertEqual(out.read_bytes(), b"payload")

    @mock.patch("dtmapi._client.requests.get")
    def test_download_to_explicit_path(self, get):
        get.side_effect, _ = self._routed_get(blob_content=b"payload")
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp) / "nga.xlsx"
            out = DTMHnaApi(subscription_key=HNA_KEY).download_hna_data(
                Admin0Pcode="NGA", Year=2022, file_path=target
            )
            self.assertEqual(out, target)
            self.assertEqual(target.read_bytes(), b"payload")

    @mock.patch("dtmapi._client.requests.get")
    def test_download_without_url_raises(self, get):
        get.return_value = fake_response({"fileName": "x.xlsx"})
        with self.assertRaises(HNAResponseError) as ctx:
            DTMHnaApi(subscription_key=HNA_KEY).download_hna_data(Admin0Pcode="NGA", Year=2022)
        self.assertIn("downloadUrl", str(ctx.exception))

    @mock.patch("dtmapi._client.requests.get")
    def test_blob_failure_names_the_file(self, get):
        get.side_effect, _ = self._routed_get(
            blob_error=requests.ConnectionError("blob unreachable")
        )
        with self.assertRaises(HNARequestError) as ctx:
            DTMHnaApi(subscription_key=HNA_KEY).download_hna_data(Admin0Pcode="NGA", Year=2022)
        self.assertIn("Report_NGA_2022", str(ctx.exception))

    def test_download_requires_the_same_params(self):
        with self.assertRaises(ValidationError):
            DTMHnaApi(subscription_key=HNA_KEY).download_hna_data(Admin0Pcode="NGA")

    # --- response shapes ---

    @mock.patch("dtmapi._client.requests.get")
    def test_handles_envelope_response(self, get):
        get.return_value = fake_response(ENVELOPE)
        df = DTMHnaApi(subscription_key=HNA_KEY).get_hna_admin2_data(
            Admin0Pcode="ETH", Year=2024
        )
        self.assertEqual(len(df), 1)

    @mock.patch("dtmapi._client.requests.get")
    def test_handles_bare_list_response(self, get):
        get.return_value = fake_response(BARE_LIST)
        df = DTMHnaApi(subscription_key=HNA_KEY).get_hna_admin2_data(
            Admin0Pcode="ETH", Year=2024
        )
        self.assertEqual(df.iloc[0]["pin"], 42)

    @mock.patch("dtmapi._client.requests.get")
    def test_empty_result_is_an_empty_frame(self, get):
        get.return_value = fake_response([])
        df = DTMHnaApi(subscription_key=HNA_KEY).get_all_countries()
        self.assertTrue(df.empty)

    @mock.patch("dtmapi._client.requests.get")
    def test_unknown_shape_raises_hna_error(self, get):
        get.return_value = fake_response({"unexpected": 1})
        with self.assertRaises(HNAResponseError) as ctx:
            DTMHnaApi(subscription_key=HNA_KEY).get_all_countries()
        self.assertIn("Unrecognised HNA response shape", str(ctx.exception))

    @mock.patch("dtmapi._client.requests.get")
    def test_apim_error_object_surfaces_its_message(self, get):
        get.return_value = fake_response({"statusCode": 404, "message": "Resource not found"})
        with self.assertRaises(HNAResponseError) as ctx:
            DTMHnaApi(subscription_key=HNA_KEY).get_all_countries()
        self.assertIn("Resource not found", str(ctx.exception))

    @mock.patch("dtmapi._client.requests.get")
    def test_catalog_returns_the_data_dictionary(self, get):
        # Shape taken from a real /HNADataCatalog response.
        get.return_value = fake_response([
            {"indicator_category": "Priority Needs",
             "indicator_name": "pct_hh_m2730_hh_priority_needs_food",
             "description": "Percentage of households reporting food as a priority need",
             "data_type": "Float"},
            {"indicator_category": "Year of assessment", "indicator_name": "year",
             "description": "Year in which the HNA assessment was conducted",
             "data_type": "Integer"},
        ])
        df = DTMHnaApi(subscription_key=HNA_KEY).get_hna_data_catalog()
        self.assertEqual(
            list(df.columns),
            ["indicator_category", "indicator_name", "description", "data_type"],
        )
        self.assertEqual(len(df), 2)


class TestExceptionUnification(unittest.TestCase):
    def test_hna_errors_are_dtm_errors(self):
        self.assertTrue(issubclass(HNAError, DTMApiError))
        self.assertTrue(issubclass(HNAResponseError, DTMApiResponseError))

    def test_single_handler_catches_both(self):
        for exc in (DTMApiResponseError("a"), HNAResponseError("b", ["b"])):
            with self.assertRaises(DTMApiError):
                raise exc

    def test_response_error_keeps_two_arg_init(self):
        e = HNAResponseError("msg", ["one", "two"])
        self.assertEqual(e.error_messages, ["one", "two"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
