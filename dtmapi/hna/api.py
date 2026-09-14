import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Union

import pandas as pd
import requests

from dtmapi._client import BaseDTMClient
from dtmapi.hna.config import (
    HNA_BASE_URLS,
    HNA_ENDPOINT_PATHS,
    SUPPORTED_ENVIRONMENTS,
    SUPPORTED_VERSIONS,
)
from dtmapi.hna.exceptions import (
    HNAAuthError,
    HNARequestError,
    HNAResponseError,
    HNATimeoutError,
    HNAVersionError,
)
from dtmapi.validators import ValidationError

# Configure logger
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class DTMHnaApi(BaseDTMClient):
    """
    Python interface to the DTM Humanitarian Needs Assessment (HNA) endpoints.

    Shares the request handling, retry behaviour and authentication of
    :class:`dtmapi.DTMApi`, but has its own endpoints, parameters and version
    line (HNA is on v1; the displacement API is on v3).

    **The HNA API has its own subscription key.** It is a separate
    subscription on the DTM gateway, so the displacement key will not work
    here and this client never falls back to it::

        dtm_api = DTMApi(subscription_key=DTM_API_KEY)
        dtm_hna = DTMHnaApi(subscription_key=DTM_HNA_KEY)

    When no key is passed, this client reads ``DTMHNA_SUBSCRIPTION_KEY`` and
    nothing else.

    **Usage:**

    ::

        hna = DTMHnaApi(subscription_key="YOUR-HNA-KEY")

        hna.get_all_countries()
        hna.get_hna_data_catalog()
        hna.get_all_hna_admin2_data(Admin0Pcode="ETH", Year=2024)
    """

    SERVICE_NAME = "DTM HNA API"
    ENV_KEY_NAME = "DTMHNA_SUBSCRIPTION_KEY"

    # Errors name the service that rejected the call. Each inherits its
    # displacement-API counterpart, so existing handlers keep working.
    AUTH_ERROR = HNAAuthError
    TIMEOUT_ERROR = HNATimeoutError
    REQUEST_ERROR = HNARequestError
    RESPONSE_ERROR = HNAResponseError

    def __init__(
        self,
        subscription_key: Optional[str] = None,
        api_version: str = "v1",
        environment: str = "dev",
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
    ):
        """
        Initialize the HNA API client.

        :param subscription_key: HNA API subscription key — separate from the
            displacement API key. Can also be set via the
            DTMHNA_SUBSCRIPTION_KEY environment variable.
        :type subscription_key: Optional[str]
        :param api_version: HNA API version to use (currently only "v1").
        :type api_version: str
        :param environment: Gateway environment to target.
        :type environment: str
        :param timeout: Request timeout in seconds (default: 30).
        :type timeout: Optional[int]
        :param max_retries: Maximum number of retry attempts for failed requests (default: 3).
        :type max_retries: Optional[int]
        :param retry_delay: Base delay in seconds between retries (default: 1). Uses exponential backoff.
        :type retry_delay: Optional[float]
        :raises HNAVersionError: If api_version or environment is not supported.
        :raises HNAAuthError: If no subscription key is provided.
        """
        if api_version not in SUPPORTED_VERSIONS:
            raise HNAVersionError(
                f"api_version must be one of {', '.join(SUPPORTED_VERSIONS)}, got: '{api_version}'"
            )
        self.api_version = api_version

        if environment not in SUPPORTED_ENVIRONMENTS:
            raise HNAVersionError(
                f"environment must be one of {', '.join(SUPPORTED_ENVIRONMENTS)}, got: '{environment}'"
            )
        self.environment = environment

        super().__init__(
            subscription_key=subscription_key,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )

        #: Pagination block from the most recent paginated response, if any.
        self._last_pagination: Optional[Dict[str, Any]] = None

        self._logger.info(
            f"DTMHnaApi client initialized with api_version={self.api_version}, "
            f"environment={self.environment}, timeout={self.timeout}s, "
            f"max_retries={self.max_retries}, retry_delay={self.retry_delay}s"
        )

    def _get_endpoint(self, endpoint_type: str) -> str:
        """
        Build the HNA endpoint URL for the configured environment.

        :param endpoint_type: One of "countries", "catalog", "admin2", "download".
        :type endpoint_type: str
        :return: The full API endpoint URL.
        :rtype: str
        """
        return f"{HNA_BASE_URLS[self.environment]}/{HNA_ENDPOINT_PATHS[endpoint_type]}"

    def _unwrap(self, data: Any) -> Any:
        """
        Pull the payload out of an HNA response.

        The gateway wraps results more than once. A real admin2 response looks
        like::

            {"result": {"result": {"data": [...], "pagination": {...}},
                        "isSuccess": true, "errorMessages": []},
             "id": 103, "exception": null, "status": 5, ...}

        So this unwraps ``result`` repeatedly, checks ``isSuccess`` and
        ``exception`` at every level it finds them, and returns the ``data``
        list. Paginated responses also stash their ``pagination`` block on
        ``self._last_pagination`` for :meth:`get_all_hna_admin2_data`.

        Endpoints that answer with a bare list are returned unchanged.
        """
        self._last_pagination = None
        seen = 0

        while isinstance(data, dict):
            if data.get("exception"):
                raise self.RESPONSE_ERROR(f"API returned an exception: {data['exception']}")

            if "isSuccess" in data and not data["isSuccess"]:
                messages = data.get("errorMessages") or []
                raise self.RESPONSE_ERROR(
                    messages[0] if messages else "Unknown API error", list(messages)
                )

            if "data" in data:
                self._last_pagination = data.get("pagination")
                payload = data["data"]
                if not isinstance(payload, list):
                    raise self.RESPONSE_ERROR(
                        f"Expected 'data' to be a list, got {type(payload).__name__}"
                    )
                return payload

            if "result" in data:
                data = data["result"]
                seen += 1
                if seen > 5:  # guard against a self-referencing payload
                    break
                continue

            # A dict with no result/data is an error body from the gateway.
            for key in ("message", "detail", "title", "error"):
                if key in data:
                    self._logger.error(f"API returned an error object: {data[key]}")
                    raise self.RESPONSE_ERROR(str(data[key]))
            break

        if isinstance(data, list):
            return data

        raise self.RESPONSE_ERROR(
            f"Unrecognised HNA response shape: {type(data).__name__} "
            f"{sorted(data) if isinstance(data, dict) else str(data)[:120]}"
        )

    # ----------- Parameter handling -----------

    @staticmethod
    def _population_group_param(
        PopulationGroup: Optional[Union[str, Iterable[str]]]
    ) -> Optional[str]:
        """
        Normalise PopulationGroup into the comma-separated string the API expects.

        Accepts a plain string (passed through) or any iterable of strings, so
        both of these work::

            PopulationGroup="IDP"
            PopulationGroup=["IDP", "IDP returnee"]

        The data dictionary describes this field (``m2788_loc_assessment_strata``)
        as the population category: IDP, IDP returnee, or non-displaced. The
        exact spellings the API accepts are not validated here, since the
        service is the authority on them.
        """
        if PopulationGroup is None:
            return None
        if isinstance(PopulationGroup, str):
            value = PopulationGroup
        else:
            value = ",".join(str(group) for group in PopulationGroup)
        value = ",".join(part.strip() for part in value.split(",") if part.strip())
        if not value:
            raise ValidationError("PopulationGroup must not be empty when provided")
        return value

    def _assessment_params(
        self,
        Admin0Pcode: Optional[str],
        Year: Optional[int],
        Admin0Name: Optional[str],
        PopulationGroup: Optional[Union[str, Iterable[str]]],
    ) -> Dict[str, Any]:
        """
        Validate and assemble the parameters shared by admin2 and download.

        Admin0Pcode and Year are both required by the API — unlike the
        displacement endpoints, where any one of several filters will do.
        """
        if not Admin0Pcode:
            raise ValidationError(
                "Admin0Pcode is required (country code, ISO 3166-1 alpha-3)"
            )
        if Year is None:
            raise ValidationError("Year is required")
        try:
            Year = int(Year)
        except (TypeError, ValueError):
            raise ValidationError(f"Year must be an integer, got: {Year!r}")

        params = {
            "Admin0Pcode": Admin0Pcode,
            "Year": Year,
            "Admin0Name": Admin0Name,
            "PopulationGroup": self._population_group_param(PopulationGroup),
        }
        return {k: v for k, v in params.items() if v is not None}

    # ----------- Public API Methods -----------

    def get_all_countries(
        self, to_pandas: bool = True
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """
        Retrieve all countries for which HNA data is available through the API.

        Takes no parameters.

        :param to_pandas: If True, the data will be returned as a pandas DataFrame. Otherwise, it will be returned as a JSON object.
        :type to_pandas: bool
        :return: All countries for which HNA data is available.
        :rtype: Union[pd.DataFrame, Dict[str, Any]]
        """
        return self._fetch_data(self._get_endpoint("countries"), to_pandas=to_pandas)

    def get_hna_data_catalog(
        self, to_pandas: bool = True
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """
        Retrieve the HNA data dictionary.

        Takes no parameters. Returns one row per indicator available in the
        Admin 2 data, with its category, machine name, description and data
        type — so this describes the *columns* you will get back from
        :meth:`get_all_hna_admin2_data`, not which countries or years exist.

        Useful for looking up what a column such as
        ``pct_hh_m2730_hh_priority_needs_food`` actually measures, or for
        filtering the Admin 2 frame down to one indicator category::

            catalog = hna.get_hna_data_catalog()
            needs = catalog[catalog["indicator_category"] == "Priority Needs"]
            data = hna.get_all_hna_admin2_data(Admin0Pcode="NGA", Year=2023)
            data[["m3695_meta_adm2_name", *needs["indicator_name"]]]

        :param to_pandas: If True, the data will be returned as a pandas DataFrame. Otherwise, it will be returned as a JSON object.
        :type to_pandas: bool
        :return: One record per indicator: indicator_category, indicator_name,
            description and data_type.
        :rtype: Union[pd.DataFrame, Dict[str, Any]]
        """
        return self._fetch_data(self._get_endpoint("catalog"), to_pandas=to_pandas)

    def get_hna_admin2_data(
        self,
        Admin0Pcode: Optional[str] = None,
        Year: Optional[int] = None,
        Admin0Name: Optional[str] = None,
        PopulationGroup: Optional[Union[str, Iterable[str]]] = None,
        Page: int = 1,
        to_pandas: bool = True,
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """
        Retrieve one page of HNA data at Admin 2 level.

        Admin0Pcode and Year are both required. This endpoint is paginated, so
        a single call returns only one page — see
        :meth:`get_all_hna_admin2_data` to walk every page.

        :param Admin0Pcode: Country code (ISO 3166-1 alpha-3). Required.
        :type Admin0Pcode: str
        :param Year: Assessment year. Required.
        :type Year: int
        :param Admin0Name: Name of the country.
        :type Admin0Name: Optional[str]
        :param PopulationGroup: One population group, a comma-separated string,
            or a list of groups.
        :type PopulationGroup: Optional[Union[str, Iterable[str]]]
        :param Page: Page number for paginated results (default: 1).
        :type Page: int
        :param to_pandas: If True, the data will be returned as a pandas DataFrame. Otherwise, it will be returned as a JSON object.
        :type to_pandas: bool

        :return: One page of HNA Admin 2 data.
        :rtype: Union[pd.DataFrame, Dict[str, Any]]
        :raises ValidationError: If Admin0Pcode or Year is missing or malformed.
        """
        params = self._assessment_params(Admin0Pcode, Year, Admin0Name, PopulationGroup)
        if Page is not None:
            params["Page"] = int(Page)
        return self._fetch_data(self._get_endpoint("admin2"), params, to_pandas)

    def get_all_hna_admin2_data(
        self,
        Admin0Pcode: Optional[str] = None,
        Year: Optional[int] = None,
        Admin0Name: Optional[str] = None,
        PopulationGroup: Optional[Union[str, Iterable[str]]] = None,
        max_pages: int = 100,
        to_pandas: bool = True,
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """
        Retrieve every page of HNA Admin 2 data for one country and year.

        Requests successive pages until one comes back empty, then combines
        them. Prefer this over :meth:`get_hna_admin2_data` unless you want to
        handle paging yourself — a single-page call silently gives you only
        the first slice of the results.

        :param Admin0Pcode: Country code (ISO 3166-1 alpha-3). Required.
        :type Admin0Pcode: str
        :param Year: Assessment year. Required.
        :type Year: int
        :param Admin0Name: Name of the country.
        :type Admin0Name: Optional[str]
        :param PopulationGroup: One population group, a comma-separated string,
            or a list of groups.
        :type PopulationGroup: Optional[Union[str, Iterable[str]]]
        :param max_pages: Safety limit on how many pages to request (default: 100).
        :type max_pages: int
        :param to_pandas: If True, the data will be returned as a pandas DataFrame. Otherwise, it will be returned as a JSON object.
        :type to_pandas: bool

        :return: All pages of HNA Admin 2 data, combined.
        :rtype: Union[pd.DataFrame, Dict[str, Any]]
        :raises ValidationError: If Admin0Pcode or Year is missing or malformed.
        """
        rows: list = []
        for page in range(1, max_pages + 1):
            batch = self.get_hna_admin2_data(
                Admin0Pcode=Admin0Pcode,
                Year=Year,
                Admin0Name=Admin0Name,
                PopulationGroup=PopulationGroup,
                Page=page,
                to_pandas=False,
            )
            rows.extend(batch)

            pagination = getattr(self, "_last_pagination", None) or {}
            if pagination:
                # The API reports whether more pages exist; believe it.
                if not pagination.get("hasNextPage"):
                    break
            elif not batch:
                # No pagination block: fall back to stopping on an empty page.
                break
        else:
            self._logger.warning(
                f"Stopped at the max_pages limit of {max_pages}; there may be more data. "
                "Raise max_pages if this country and year is genuinely this large."
            )
        self._logger.info(f"Fetched {len(rows)} records for {Admin0Pcode} {Year}")
        return pd.DataFrame(rows) if to_pandas else rows

    def get_hna_download_url(
        self,
        Admin0Pcode: Optional[str] = None,
        Year: Optional[int] = None,
        Admin0Name: Optional[str] = None,
        PopulationGroup: Optional[Union[str, Iterable[str]]] = None,
    ) -> Dict[str, Any]:
        """
        Ask the API to prepare an export file and return a pointer to it.

        The download endpoint does not return the file itself. It returns a
        short-lived link to blob storage::

            {"downloadUrl": "https://...blob.core.windows.net/.../Report_NGA_2022_....xlsx",
             "fileName": "Report_NGA_2022__20260914101710.xlsx",
             "expiresAt": "2026-09-14T10:27:10.675+00:00"}

        Use :meth:`download_hna_data` to get the bytes in one call. Use this
        method when you want the link itself — to hand it to a browser, for
        example.

        :param Admin0Pcode: Country code (ISO 3166-1 alpha-3). Required.
        :type Admin0Pcode: str
        :param Year: Assessment year. Required.
        :type Year: int
        :param Admin0Name: Name of the country.
        :type Admin0Name: Optional[str]
        :param PopulationGroup: One population group, a comma-separated string,
            or a list of groups.
        :type PopulationGroup: Optional[Union[str, Iterable[str]]]

        :return: The download pointer, with an added ``expires_at`` datetime
            when the API's timestamp could be parsed.
        :rtype: Dict[str, Any]
        :raises ValidationError: If Admin0Pcode or Year is missing or malformed.
        :raises HNAResponseError: If the response has no downloadUrl.
        """
        params = self._assessment_params(Admin0Pcode, Year, Admin0Name, PopulationGroup)
        info = self._fetch_data(
            self._get_endpoint("download"), params, to_pandas=False, unwrap=False
        )

        if not isinstance(info, dict) or not info.get("downloadUrl"):
            raise self.RESPONSE_ERROR(
                f"The download endpoint returned no downloadUrl: {str(info)[:200]}"
            )

        expires_at = self._parse_expiry(info.get("expiresAt"))
        if expires_at is not None:
            info = {**info, "expires_at": expires_at}
        return info

    @staticmethod
    def _parse_expiry(value: Optional[str]) -> Optional[datetime]:
        """
        Parse the API's expiresAt timestamp.

        .NET writes seven fractional digits, which ``fromisoformat`` rejects,
        so the fraction is trimmed to microseconds first.
        """
        if not value:
            return None
        cleaned = re.sub(r"(\.\d{6})\d+", r"\1", value)
        try:
            return datetime.fromisoformat(cleaned)
        except ValueError:
            return None

    def download_hna_data(
        self,
        Admin0Pcode: Optional[str] = None,
        Year: Optional[int] = None,
        Admin0Name: Optional[str] = None,
        PopulationGroup: Optional[Union[str, Iterable[str]]] = None,
        file_path: Optional[Union[str, Path]] = None,
    ) -> Union[bytes, Path]:
        """
        Download the HNA export file for one country and year.

        Two requests: the API prepares the file and returns a short-lived blob
        link (about ten minutes), which is then fetched. The blob is on a
        different host, so the subscription key is deliberately not sent with
        the second request.

        The file is an ``.xlsx`` workbook, so it is returned as bytes rather
        than a DataFrame. To read it::

            path = hna.download_hna_data(Admin0Pcode="NGA", Year=2022, file_path=".")
            df = pd.read_excel(path)

        :param Admin0Pcode: Country code (ISO 3166-1 alpha-3). Required.
        :type Admin0Pcode: str
        :param Year: Assessment year. Required.
        :type Year: int
        :param Admin0Name: Name of the country.
        :type Admin0Name: Optional[str]
        :param PopulationGroup: One population group, a comma-separated string,
            or a list of groups.
        :type PopulationGroup: Optional[Union[str, Iterable[str]]]
        :param file_path: Where to write the file. Pass a directory to use the
            API's own file name. If omitted, the bytes are returned instead.
        :type file_path: Optional[Union[str, Path]]

        :return: The path written to, or the file contents as bytes.
        :rtype: Union[bytes, Path]
        :raises ValidationError: If Admin0Pcode or Year is missing or malformed.
        :raises HNAResponseError: If the response has no downloadUrl.
        :raises HNARequestError: If the blob cannot be fetched.
        """
        info = self.get_hna_download_url(
            Admin0Pcode=Admin0Pcode,
            Year=Year,
            Admin0Name=Admin0Name,
            PopulationGroup=PopulationGroup,
        )
        url = info["downloadUrl"]
        file_name = info.get("fileName") or "hna_export.xlsx"

        expires_at = info.get("expires_at")
        if expires_at is not None and expires_at <= datetime.now(timezone.utc):
            self._logger.warning(
                f"The download link expired at {expires_at.isoformat()}; fetching anyway."
            )

        self._logger.debug(f"Fetching the export file from blob storage: {file_name}")
        try:
            # No subscription key here: the blob is on a different host and the
            # link already carries its own access token.
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as e:
            raise self.REQUEST_ERROR(f"Failed to download {file_name}: {e}") from e

        content = response.content
        self._logger.info(f"Downloaded {file_name} ({len(content)} bytes)")

        if file_path is None:
            return content

        path = Path(file_path)
        if path.is_dir():
            path = path / file_name
        path.write_bytes(content)
        self._logger.info(f"Wrote {len(content)} bytes to {path}")
        return path
