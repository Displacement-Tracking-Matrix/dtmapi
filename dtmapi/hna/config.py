"""
Endpoint URLs for the HNA API.

Query parameters accepted by each endpoint::

    country-list  (none)
    catalog       (none)
    admin2        Admin0Name, Admin0Pcode, PopulationGroup, Year, Page
    download      Admin0Name, Admin0Pcode, PopulationGroup, Year
"""

HNA_COUNTRY_LIST_API = "https://dtmapi.iom.int/HNA/v1/country-list"
HNA_CATALOG_API = "https://dtmapi.iom.int/HNA/v1/catalog"
HNA_ADMIN_2_API = "https://dtmapi.iom.int/HNA/v1/admin2"
HNA_DOWNLOAD_API = "https://dtmapi.iom.int/HNA/v1/download"

SUPPORTED_VERSIONS = ("v1",)
