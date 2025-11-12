"""Input validation utilities for DTM API."""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional


class ValidationError(ValueError):
    """Raised when input validation fails."""

    pass


def validate_date_format(date_string: str, param_name: str) -> None:
    """
    Validate that a date string is in YYYY-MM-DD format.

    :param date_string: The date string to validate.
    :type date_string: str
    :param param_name: The parameter name for error messages.
    :type param_name: str
    :raises ValidationError: If date format is invalid.
    """
    if not date_string:
        return

    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    if not date_pattern.match(date_string):
        raise ValidationError(
            f"{param_name} must be in YYYY-MM-DD format, got: {date_string}"
        )

    try:
        datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError as e:
        raise ValidationError(f"{param_name} is not a valid date: {e}") from e


def validate_date_range(
    from_date: Optional[str], to_date: Optional[str], from_param: str, to_param: str
) -> None:
    """
    Validate that date range is logical (from_date <= to_date).

    :param from_date: Start date string.
    :type from_date: Optional[str]
    :param to_date: End date string.
    :type to_date: Optional[str]
    :param from_param: Name of the from parameter.
    :type from_param: str
    :param to_param: Name of the to parameter.
    :type to_param: str
    :raises ValidationError: If date range is invalid.
    """
    if not from_date or not to_date:
        return

    from_dt = datetime.strptime(from_date, "%Y-%m-%d")
    to_dt = datetime.strptime(to_date, "%Y-%m-%d")

    if from_dt > to_dt:
        raise ValidationError(
            f"{from_param} ({from_date}) must be before or equal to {to_param} ({to_date})"
        )


def validate_round_number_range(
    from_round: Optional[int], to_round: Optional[int]
) -> None:
    """
    Validate round number range.

    :param from_round: Starting round number.
    :type from_round: Optional[int]
    :param to_round: Ending round number.
    :type to_round: Optional[int]
    :raises ValidationError: If range is invalid.
    """
    if from_round is not None and from_round < 1:
        raise ValidationError(f"FromRoundNumber must be >= 1, got: {from_round}")

    if to_round is not None and to_round < 1:
        raise ValidationError(f"ToRoundNumber must be >= 1, got: {to_round}")

    if from_round is not None and to_round is not None and from_round > to_round:
        raise ValidationError(
            f"FromRoundNumber ({from_round}) must be <= ToRoundNumber ({to_round})"
        )


def validate_required_params(
    params: Dict[str, Any], required_one_of: List[str]
) -> None:
    """
    Validate that at least one of the required parameters is provided.

    :param params: Dictionary of parameters.
    :type params: Dict[str, Any]
    :param required_one_of: List of parameter names where at least one is required.
    :type required_one_of: List[str]
    :raises ValidationError: If no required parameters are provided.
    """
    if not any(params.get(param) is not None for param in required_one_of):
        raise ValidationError(
            f"At least one of the following parameters is required: {', '.join(required_one_of)}"
        )
