"""Unit tests for validators."""

import unittest

from dtmapi.validators import (
    ValidationError,
    validate_date_format,
    validate_date_range,
    validate_required_params,
    validate_round_number_range,
)


class TestValidateDateFormat(unittest.TestCase):
    """Test date format validation."""

    def test_valid_date(self):
        """Test validation with valid date."""
        validate_date_format("2024-01-15", "TestDate")  # Should not raise

    def test_invalid_format(self):
        """Test validation with invalid format."""
        with self.assertRaises(ValidationError) as context:
            validate_date_format("01-15-2024", "TestDate")
        self.assertIn("YYYY-MM-DD", str(context.exception))

    def test_invalid_date(self):
        """Test validation with invalid date."""
        with self.assertRaises(ValidationError) as context:
            validate_date_format("2024-13-01", "TestDate")
        self.assertIn("not a valid date", str(context.exception))

    def test_empty_string(self):
        """Test validation with empty string."""
        validate_date_format("", "TestDate")  # Should not raise


class TestValidateDateRange(unittest.TestCase):
    """Test date range validation."""

    def test_valid_range(self):
        """Test validation with valid range."""
        validate_date_range("2024-01-01", "2024-12-31", "FromDate", "ToDate")  # Should not raise

    def test_same_dates(self):
        """Test validation with same dates."""
        validate_date_range("2024-01-01", "2024-01-01", "FromDate", "ToDate")  # Should not raise

    def test_invalid_range(self):
        """Test validation with invalid range (from > to)."""
        with self.assertRaises(ValidationError) as context:
            validate_date_range("2024-12-31", "2024-01-01", "FromDate", "ToDate")
        self.assertIn("must be before or equal to", str(context.exception))

    def test_none_from_date(self):
        """Test validation with None from date."""
        validate_date_range(None, "2024-12-31", "FromDate", "ToDate")  # Should not raise

    def test_none_to_date(self):
        """Test validation with None to date."""
        validate_date_range("2024-01-01", None, "FromDate", "ToDate")  # Should not raise

    def test_both_none(self):
        """Test validation with both dates None."""
        validate_date_range(None, None, "FromDate", "ToDate")  # Should not raise


class TestValidateRoundNumberRange(unittest.TestCase):
    """Test round number range validation."""

    def test_valid_range(self):
        """Test validation with valid range."""
        validate_round_number_range(1, 10)  # Should not raise

    def test_same_numbers(self):
        """Test validation with same numbers."""
        validate_round_number_range(5, 5)  # Should not raise

    def test_invalid_range(self):
        """Test validation with invalid range (from > to)."""
        with self.assertRaises(ValidationError) as context:
            validate_round_number_range(10, 1)
        self.assertIn("must be <=", str(context.exception))

    def test_negative_from_round(self):
        """Test validation with negative from round."""
        with self.assertRaises(ValidationError) as context:
            validate_round_number_range(-1, 10)
        self.assertIn("must be >= 1", str(context.exception))

    def test_zero_from_round(self):
        """Test validation with zero from round."""
        with self.assertRaises(ValidationError) as context:
            validate_round_number_range(0, 10)
        self.assertIn("must be >= 1", str(context.exception))

    def test_negative_to_round(self):
        """Test validation with negative to round."""
        with self.assertRaises(ValidationError) as context:
            validate_round_number_range(1, -1)
        self.assertIn("must be >= 1", str(context.exception))

    def test_none_from_round(self):
        """Test validation with None from round."""
        validate_round_number_range(None, 10)  # Should not raise

    def test_none_to_round(self):
        """Test validation with None to round."""
        validate_round_number_range(1, None)  # Should not raise

    def test_both_none(self):
        """Test validation with both None."""
        validate_round_number_range(None, None)  # Should not raise


class TestValidateRequiredParams(unittest.TestCase):
    """Test required parameters validation."""

    def test_one_param_present(self):
        """Test validation with one required param present."""
        params = {"Operation": "IDP", "CountryName": None, "Admin0Pcode": None}
        validate_required_params(params, ["Operation", "CountryName", "Admin0Pcode"])  # Should not raise

    def test_all_params_present(self):
        """Test validation with all params present."""
        params = {"Operation": "IDP", "CountryName": "Ethiopia", "Admin0Pcode": "ETH"}
        validate_required_params(params, ["Operation", "CountryName", "Admin0Pcode"])  # Should not raise

    def test_no_params_present(self):
        """Test validation with no required params present."""
        params = {"Operation": None, "CountryName": None, "Admin0Pcode": None}
        with self.assertRaises(ValidationError) as context:
            validate_required_params(params, ["Operation", "CountryName", "Admin0Pcode"])
        self.assertIn("At least one", str(context.exception))

    def test_empty_dict(self):
        """Test validation with empty dict."""
        params = {}
        with self.assertRaises(ValidationError) as context:
            validate_required_params(params, ["Operation", "CountryName"])
        self.assertIn("At least one", str(context.exception))


if __name__ == "__main__":
    unittest.main()
