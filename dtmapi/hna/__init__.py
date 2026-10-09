"""
Humanitarian Needs Assessment (HNA) client for the DTM API.

Ships inside :mod:`dtmapi` so one install covers both services::

    from dtmapi import DTMApi, DTMHnaApi
"""

from dtmapi.hna.api import DTMHnaApi
from dtmapi.hna.exceptions import (
    HNAAuthError,
    HNAError,
    HNARequestError,
    HNAResponseError,
    HNATimeoutError,
    HNAVersionError,
)

__all__ = [
    "DTMHnaApi",
    "HNAError",
    "HNARequestError",
    "HNAResponseError",
    "HNATimeoutError",
    "HNAVersionError",
    "HNAAuthError",
]
