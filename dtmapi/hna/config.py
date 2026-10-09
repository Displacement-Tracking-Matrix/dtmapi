"""
Endpoint configuration for the HNA API.

The HNA endpoints sit behind a different gateway host from the displacement
API, so the URLs are built here rather than derived from ``dtmapi/config.py``.

Verified against the API portal:
    https://dtm-apim-dev.iom.int/HNA/v1/CountryList
"""

#: Gateway base URL per environment.
HNA_BASE_URLS = {
    "prod": "https://dtm-apim.iom.int/HNA/v1",
    "dev": "https://dtm-apim-dev.iom.int/HNA/v1",
}

#: Path segment for each endpoint, appended to the environment's base URL.
HNA_ENDPOINT_PATHS = {
    "countries": "CountryList",
    "catalog": "HNADataCatalog",
    "admin2": "admin2",
    "download": "download",
}

SUPPORTED_VERSIONS = ("v1",)
SUPPORTED_ENVIRONMENTS = tuple(HNA_BASE_URLS)
