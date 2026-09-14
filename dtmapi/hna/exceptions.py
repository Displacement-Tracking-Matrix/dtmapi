"""
Exceptions for the HNA client.

Every one of these inherits from :class:`dtmapi.exceptions.DTMApiError`, so a
caller working with both clients can write a single handler::

    from dtmapi import DTMApi, DTMHnaApi
    from dtmapi.exceptions import DTMApiError

    try:
        idp = DTMApi().get_idp_admin0_data(CountryName="Chad")
        hna = DTMHnaApi().get_hna_admin2_data(CountryName="Chad")
    except DTMApiError as exc:
        ...

Inheriting only ever widens what an existing ``except`` clause catches, so no
current dtmapi user is affected.
"""

from dtmapi.exceptions import (
    DTMApiError,
    DTMApiRequestError,
    DTMApiResponseError,
    DTMApiTimeoutError,
    DTMApiVersionError,
    DTMAuthenticationError,
)


class HNAError(DTMApiError):
    """Base exception for HNA API errors."""


class HNARequestError(HNAError, DTMApiRequestError):
    """Raised when a request to the HNA API fails."""


class HNAResponseError(HNAError, DTMApiResponseError):
    """Raised when the HNA API returns an error response."""


class HNATimeoutError(HNAError, DTMApiTimeoutError):
    """Raised when a request to the HNA API times out."""


class HNAVersionError(HNAError, DTMApiVersionError):
    """Raised when an invalid HNA API version is specified."""


class HNAAuthError(HNAError, DTMAuthenticationError):
    """Raised when authentication with the HNA API fails."""
