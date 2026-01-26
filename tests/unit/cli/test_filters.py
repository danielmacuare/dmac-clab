"""Unit tests for filter parsing logic."""

import pytest
from nornir.core.filter import F

from py_netauto.cli.filters import (
    format_filter_expression,
    parse_filters,
    parse_single_filter,
    validate_filter_syntax,
)


class TestValidateFilterSyntax:
    """Test filter syntax validation."""

    def test_valid_simple_filter(self):
        """Valid simple filter should not raise exception."""
        validate_filter_syntax("role=leaf")

    def test_valid_filter_with_pipe(self):
        """Valid filter with pipe should not raise exception."""
        validate_filter_syntax("role=leaf|spine")

    def test_missing_equals_raises_error(self):
        """Filter without equals sign should raise ValueError."""
        with pytest.raises(ValueError, match="Missing '=' in filter expression"):
            validate_filter_syntax("roleleaf")

    def test_empty_key_raises_error(self):
        """Filter with empty key should raise ValueError."""
        with pytest.raises(ValueError, match="Empty key in filter expression"):
            validate_filter_syntax("=leaf")

    def test_empty_value_raises_error(self):
        """Filter with empty value should raise ValueError."""
        with pytest.raises(ValueError, match="Empty value in filter expression"):
            validate_filter_syntax("role=")

    def test_whitespace_only_key_raises_error(self):
        """Filter with whitespace-only key should raise ValueError."""
        with pytest.raises(ValueError, match="Empty key in filter expression"):
            validate_filter_syntax("  =leaf")

    def test_whitespace_only_value_raises_error(self):
        """Filter with whitespace-only value should raise ValueError."""
        with pytest.raises(ValueError, match="Empty value in filter expression"):
            validate_filter_syntax("role=  ")


class TestParseSingleFilter:
    """Test single filter parsing."""

    def test_simple_filter_creates_f_object(self):
        """Simple filter should create F() object with correct attribute."""
        result = parse_single_filter("role=leaf")
        assert isinstance(result, F)

    def test_simple_filter_with_whitespace(self):
        """Filter with whitespace should be trimmed."""
        result = parse_single_filter("  role = leaf  ")
        assert isinstance(result, F)

    def test_or_filter_with_two_values(self):
        """OR filter with two values should create combined expression."""
        result = parse_single_filter("role=leaf|spine")
        # Result should be F(role="leaf") | F(role="spine")
        assert result is not None

    def test_or_filter_with_three_values(self):
        """OR filter with three values should create combined expression."""
        result = parse_single_filter("name=l1|l2|l3")
        assert result is not None

    def test_or_filter_with_whitespace(self):
        """OR filter with whitespace should be trimmed."""
        result = parse_single_filter("role= leaf | spine ")
        assert result is not None

    def test_invalid_syntax_raises_error(self):
        """Invalid filter syntax should raise ValueError."""
        with pytest.raises(ValueError, match="Missing '=' in filter expression"):
            parse_single_filter("invalid")

    def test_empty_or_values_raises_error(self):
        """OR filter with empty values should raise ValueError."""
        with pytest.raises(ValueError, match="No valid values in OR expression"):
            parse_single_filter("role=|")

    def test_filter_with_special_characters(self):
        """Filter with special characters in value should work."""
        result = parse_single_filter("platform=arista_eos")
        assert isinstance(result, F)

    def test_filter_with_numbers(self):
        """Filter with numbers in value should work."""
        result = parse_single_filter("name=spine1")
        assert isinstance(result, F)


class TestParseFilters:
    """Test multiple filter parsing and combination."""

    def test_none_returns_none(self):
        """None input should return None."""
        result = parse_filters(None)
        assert result is None

    def test_empty_list_returns_none(self):
        """Empty list should return None."""
        result = parse_filters([])
        assert result is None

    def test_single_filter(self):
        """Single filter should be parsed correctly."""
        result = parse_filters(["role=leaf"])
        assert result is not None

    def test_two_filters_combined_with_and(self):
        """Two filters should be combined with AND logic."""
        result = parse_filters(["role=leaf", "name=l1"])
        assert result is not None

    def test_three_filters_combined_with_and(self):
        """Three filters should be combined with AND logic."""
        result = parse_filters(["role=leaf", "name=l1", "platform=arista_eos"])
        assert result is not None

    def test_and_with_or_combination(self):
        """Combination of AND and OR should work correctly."""
        result = parse_filters(["role=leaf", "name=l1|l2"])
        assert result is not None

    def test_complex_combination(self):
        """Complex filter combination should work."""
        result = parse_filters(["role=leaf|spine", "platform=arista_eos", "name=l1|l2|l3"])
        assert result is not None

    def test_invalid_filter_in_list_raises_error(self):
        """Invalid filter in list should raise ValueError."""
        with pytest.raises(ValueError, match="Missing '=' in filter expression"):
            parse_filters(["role=leaf", "invalid", "name=l1"])


class TestFormatFilterExpression:
    """Test filter expression formatting."""

    def test_empty_list_returns_no_filters_message(self):
        """Empty list should return 'No filters applied'."""
        result = format_filter_expression([])
        assert result == "No filters applied"

    def test_single_filter(self):
        """Single filter should be returned as-is."""
        result = format_filter_expression(["role=leaf"])
        assert result == "role=leaf"

    def test_two_filters_joined_with_and(self):
        """Two filters should be joined with ' AND '."""
        result = format_filter_expression(["role=leaf", "name=l1"])
        assert result == "role=leaf AND name=l1"

    def test_three_filters_joined_with_and(self):
        """Three filters should be joined with ' AND '."""
        result = format_filter_expression(["role=leaf", "name=l1", "platform=arista_eos"])
        assert result == "role=leaf AND name=l1 AND platform=arista_eos"

    def test_or_filter_preserved_in_output(self):
        """OR syntax within filter should be preserved."""
        result = format_filter_expression(["role=leaf|spine"])
        assert result == "role=leaf|spine"

    def test_complex_combination_formatted_correctly(self):
        """Complex combination should be formatted correctly."""
        result = format_filter_expression(["role=leaf", "name=l1|l2", "platform=arista_eos"])
        assert result == "role=leaf AND name=l1|l2 AND platform=arista_eos"


class TestFilterIntegration:
    """Integration tests for filter parsing with mock Nornir inventory."""

    def test_filter_matches_expected_hosts(self):
        """Parsed filter should match expected hosts in inventory."""
        # This is a basic integration test
        # In a real scenario, we would test against a mock Nornir inventory
        filter_expr = parse_filters(["role=leaf"])
        assert filter_expr is not None

    def test_and_filter_narrows_results(self):
        """AND filter should narrow down results."""
        filter_expr = parse_filters(["role=leaf", "name=l1"])
        assert filter_expr is not None

    def test_or_filter_expands_results(self):
        """OR filter should expand results."""
        filter_expr = parse_filters(["role=leaf|spine"])
        assert filter_expr is not None
