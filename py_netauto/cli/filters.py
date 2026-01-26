"""
Filter parsing logic for CLI operations.

This module converts CLI filter strings into Nornir F() filter expressions,
supporting both AND and OR operations for flexible device targeting.

"""

from typing import cast

from nornir.core.filter import AND, OR, F


def validate_filter_syntax(filter_str: str) -> None:
    """
        Validate filter string syntax before parsing.

        Checks that the filter string follows the required format: key=value.
        Ensures both key and value are non-empty after splitting.

    Args:
            filter_str: Filter string to validate (e.g., "role=leaf").

    Raises:
            ValueError: If filter syntax is invalid (missing '=', empty key/value).

    Example:
    python
            validate_filter_syntax("role=leaf")  # Valid, no exception
            validate_filter_syntax("roleleaf")  # Raises ValueError
            validate_filter_syntax("=leaf")  # Raises ValueError
            validate_filter_syntax("role=")  # Raises ValueError





    """
    if "=" not in filter_str:
        msg = f"Invalid filter syntax: Missing '=' in filter expression '{filter_str}'"
        raise ValueError(msg)

    key, _, value = filter_str.partition("=")

    if not key.strip():
        msg = f"Invalid filter syntax: Empty key in filter expression '{filter_str}'"
        raise ValueError(msg)

    if not value.strip():
        msg = f"Invalid filter syntax: Empty value in filter expression '{filter_str}'"
        raise ValueError(msg)


def parse_single_filter(filter_str: str) -> F | OR:
    """
        Parse a single filter string into an F() expression.

        Converts a CLI filter string into a Nornir F() filter object. Supports
        simple filters (key=value) and OR operations using pipe separator (key=val1|val2).

    Args:
            filter_str: Filter string to parse (e.g., "role=leaf" or "role=leaf|spine").

    Returns:
            Nornir F() filter expression (F or OR type).

    Raises:
            ValueError: If filter syntax is invalid.

    Example:
    python
            # Simple filter
            f = parse_single_filter("role=leaf")
            # Returns: F(role="leaf")

            # OR filter
            f = parse_single_filter("role=leaf|spine")
            # Returns: F(role="leaf") | F(role="spine")

            # Multiple OR values
            f = parse_single_filter("name=l1|l2|l3")
            # Returns: F(name="l1") | F(name="l2") | F(name="l3")





    """
    # Validate syntax first
    validate_filter_syntax(filter_str)

    # Split on '=' to get key and value
    key, _, value = filter_str.partition("=")
    key = key.strip()
    value = value.strip()

    # Check if value contains OR operator (pipe)
    if "|" in value:
        # Split on pipe and create F() for each value
        values = [v.strip() for v in value.split("|") if v.strip()]

        if not values:
            msg = f"Invalid filter syntax: No valid values in OR expression '{filter_str}'"
            raise ValueError(msg)

        # Create F() for first value
        filter_expr: F | OR = F(**{key: values[0]})

        # Combine remaining values with OR operator
        for val in values[1:]:
            filter_expr = filter_expr | F(**{key: val})

        return filter_expr

    # Simple filter without OR
    return F(**{key: value})


def parse_filters(filter_strings: list[str] | None) -> F | OR | AND | None:
    """
        Parse multiple filter strings and combine with AND logic.

        Converts a list of CLI filter strings into a single Nornir F() filter expression
        by combining them with AND logic. Each filter string is parsed individually and
        then combined using the & operator.

    Args:
            filter_strings: List of filter strings from CLI (e.g., ["role=leaf", "name=l1"]).

    Returns:
            Combined Nornir F() filter expression, or None if no filters provided.

    Example:
    python
            # Single filter
            f = parse_filters(["role=leaf"])
            # Returns: F(role="leaf")

            # Multiple filters (AND)
            f = parse_filters(["role=leaf", "name=l1"])
            # Returns: F(role="leaf") & F(name="l1")

            # Complex combination (AND + OR)
            f = parse_filters(["role=leaf", "name=l1|l2"])
            # Returns: F(role="leaf") & (F(name="l1") | F(name="l2"))

            # No filters
            f = parse_filters(None)
            # Returns: None





    """
    if not filter_strings:
        return None

    # Parse first filter
    combined_filter: F | OR | AND = parse_single_filter(filter_strings[0])

    # Combine remaining filters with AND operator
    for filter_str in filter_strings[1:]:
        single_filter = parse_single_filter(filter_str)
        # Type checker doesn't recognize __and__ on union types, but it exists at runtime
        combined_filter = cast("F | OR | AND", combined_filter & single_filter)  # type: ignore[operator]

    return combined_filter


def format_filter_expression(filter_strings: list[str]) -> str:
    """
        Create human-readable filter text from filter strings.

        Converts a list of filter strings into a readable format for display to users.
        Multiple filters are joined with " AND " to show the combination logic.

    Args:
            filter_strings: List of filter strings from CLI.

    Returns:
            Human-readable filter expression string.

    Example:
    python
            # Single filter
            text = format_filter_expression(["role=leaf"])
            # Returns: "role=leaf"

            # Multiple filters
            text = format_filter_expression(["role=leaf", "name=l1"])
            # Returns: "role=leaf AND name=l1"

            # Complex filters
            text = format_filter_expression(["role=leaf", "name=l1|l2", "platform=arista_eos"])
            # Returns: "role=leaf AND name=l1|l2 AND platform=arista_eos"

            # Empty list
            text = format_filter_expression([])
            # Returns: "No filters applied"





    """
    if not filter_strings:
        return "No filters applied"

    return " AND ".join(filter_strings)
