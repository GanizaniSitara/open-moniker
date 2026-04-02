"""Moniker parsing utilities."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

from .types import Moniker, MonikerPath, QueryParams


class MonikerParseError(ValueError):
    """Raised when a moniker string cannot be parsed."""
    pass


# Valid segment pattern: alphanumeric, hyphens, underscores, dots
# Must start with alphanumeric
SEGMENT_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.\-]*$")

# Namespace pattern: alphanumeric, hyphens, underscores (no dots - those are for paths)
NAMESPACE_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_\-]*$")

# Segment identity pattern: valid chars for the @id value within a path segment
SEGMENT_ID_VALUE_PATTERN = re.compile(r"^[a-zA-Z0-9_.\-]+$")

# Revision pattern: /vN or /VN where N is a positive integer (case-insensitive)
REVISION_PATTERN = re.compile(r"^[vV](\d+)$")

# date@VALUE patterns: absolute (YYYYMMDD), relative (3M, 1Y, 5D), symbolic (latest, previous)
DATE_PARAM_PATTERN = re.compile(
    r"^(?:\d{8}|[1-9]\d*[YMWD]|latest|previous)$",
    re.IGNORECASE,
)


def validate_segment(segment: str) -> bool:
    """Check if a path segment is valid."""
    if not segment:
        return False
    if len(segment) > 128:
        return False
    return bool(SEGMENT_PATTERN.match(segment))


def validate_namespace(namespace: str) -> bool:
    """Check if a namespace is valid."""
    if not namespace:
        return False
    if len(namespace) > 64:
        return False
    return bool(NAMESPACE_PATTERN.match(namespace))


def parse_path(path_str: str, *, validate: bool = True) -> MonikerPath:
    """
    Parse a path string into a MonikerPath.

    Args:
        path_str: Path string like "indices.sovereign/developed/EUR"
        validate: Whether to validate segment names

    Returns:
        MonikerPath instance

    Raises:
        MonikerParseError: If path is invalid
    """
    if not path_str or path_str == "/":
        return MonikerPath.root()

    # Strip leading/trailing slashes
    clean = path_str.strip("/")
    if not clean:
        return MonikerPath.root()

    segments = clean.split("/")

    if validate:
        for seg in segments:
            if not validate_segment(seg):
                raise MonikerParseError(
                    f"Invalid path segment: '{seg}'. "
                    "Segments must start with alphanumeric and contain only "
                    "alphanumerics, hyphens, underscores, or dots."
                )

    return MonikerPath(tuple(segments))


def parse_moniker(moniker_str: str, *, validate: bool = True) -> Moniker:
    """
    Parse a full moniker string.

    Format: [namespace@]path/segments[/vN][?query=params]

    The @ character within a path segment denotes an identity parameter:
        holdings/positions@ACC001/summary

    Args:
        moniker_str: The moniker string to parse
        validate: Whether to validate segment names

    Returns:
        Moniker instance

    Raises:
        MonikerParseError: If moniker is invalid
    """
    if not moniker_str:
        raise MonikerParseError("Empty moniker string")

    moniker_str = moniker_str.strip()

    # Handle scheme
    if moniker_str.startswith("moniker://"):
        # Parse as URL
        parsed = urlparse(moniker_str)
        body = parsed.netloc + parsed.path
        query_str = parsed.query
    elif "://" in moniker_str:
        raise MonikerParseError(
            f"Invalid scheme. Expected 'moniker://' or no scheme, got: {moniker_str}"
        )
    else:
        # No scheme - check for query string
        if "?" in moniker_str:
            body, query_str = moniker_str.split("?", 1)
        else:
            body = moniker_str
            query_str = ""

    # Parse namespace (prefix before first @, but only if @ appears before first /)
    namespace = None
    remaining = body

    # Check for namespace@ prefix
    # The @ must appear before any / to be a namespace (otherwise it's an identity param)
    first_at = body.find("@")
    first_slash = body.find("/")

    if first_at != -1 and (first_slash == -1 or first_at < first_slash):
        # This @ is a namespace prefix
        namespace = body[:first_at]
        remaining = body[first_at + 1:]

        if validate and not validate_namespace(namespace):
            raise MonikerParseError(
                f"Invalid namespace: '{namespace}'. "
                "Namespace must start with a letter and contain only "
                "alphanumerics, hyphens, or underscores."
            )

    # Parse revision suffix (/vN or /VN at the end - case-insensitive)
    revision = None
    remaining_lower = remaining.lower()
    if "/v" in remaining_lower:
        lower_idx = remaining_lower.rfind("/v")
        if lower_idx != -1:
            before = remaining[:lower_idx]
            after = remaining[lower_idx + 2:]  # Skip the "/v" or "/V"
            rev_match = re.match(r"^(\d+)(?:$|(?=\?))", after)
            if rev_match:
                revision = int(rev_match.group(1))
                remaining = before

    # Extract date@VALUE from final segment (reserved segment, checked first).
    # "date" is a globally hard-reserved segment name — the parser recognises it
    # before falling through to entity @id logic. It does NOT count against
    # the one-@id-per-path limit.
    date_param = None
    if "@" in remaining:
        parts = remaining.split("/")
        final = parts[-1]
        if final.startswith("date@"):
            date_value = final[5:]  # strip "date@"
            if not date_value:
                raise MonikerParseError("Empty date value in 'date@'.")
            if validate and not DATE_PARAM_PATTERN.match(date_value):
                raise MonikerParseError(
                    f"Invalid date parameter: '{date_value}'. "
                    "Must be YYYYMMDD, relative (e.g., 3M, 1Y, 5D), "
                    "or symbolic (latest, previous)."
                )
            date_param = date_value
            # Remove the date segment from the path
            parts = parts[:-1]
            remaining = "/".join(parts)

    # Extract in-path segment identity (@id embedded in a path segment).
    # @ is ONLY valid as an identity parameter within a segment followed by more path.
    # @ at end of path or standalone is a parse error (unless it was a date@ segment,
    # already consumed above).
    segment_id = None
    if "@" in remaining:
        parts = remaining.split("/")
        at_segments = [(i, p) for i, p in enumerate(parts) if "@" in p]

        if not at_segments:
            pass  # No @ after splitting — shouldn't happen but safe
        else:
            # Segment identity: @ appears in a segment that is NOT the last one
            mid_at = [(i, p) for i, p in at_segments if i < len(parts) - 1]

            # @ in the final segment is now a parse error (no more @version syntax)
            final_at = [(i, p) for i, p in at_segments if i == len(parts) - 1]
            if final_at:
                raise MonikerParseError(
                    f"Invalid use of '@' at end of path in '{final_at[0][1]}'. "
                    "The @ character is only valid as an identity parameter "
                    "within a mid-path segment (e.g., segment@id/rest)."
                )

            if mid_at:
                if len(mid_at) > 1:
                    raise MonikerParseError(
                        "At most one @id identity parameter is allowed per path."
                    )
                seg_idx, seg_text = mid_at[0]
                seg_name, seg_id_value = seg_text.split("@", 1)

                if not seg_id_value:
                    raise MonikerParseError(
                        f"Empty @id value in segment '{seg_text}'."
                    )
                if validate and not SEGMENT_ID_VALUE_PATTERN.match(seg_id_value):
                    raise MonikerParseError(
                        f"Invalid segment identity value: '{seg_id_value}'. "
                        "Must contain only alphanumerics, hyphens, underscores, or dots."
                    )

                segment_id = (seg_idx, seg_id_value)
                # Replace the segment with the clean name (without @id) for catalog lookup
                parts[seg_idx] = seg_name
                remaining = "/".join(parts)

    # Parse path
    path = parse_path(remaining, validate=validate)

    # Parse query params
    params: dict[str, str] = {}
    if query_str:
        parsed_qs = parse_qs(query_str, keep_blank_values=True)
        for key, values in parsed_qs.items():
            if values:
                params[key] = values[0]

    return Moniker(
        path=path,
        namespace=namespace,
        segment_id=segment_id,
        date_param=date_param,
        revision=revision,
        params=QueryParams(params),
    )


def normalize_moniker(moniker_str: str) -> str:
    """
    Normalize a moniker string to canonical form.

    Always returns: moniker://[namespace@]path[/vN][?sorted_params]
    """
    m = parse_moniker(moniker_str)
    return str(m)


def build_moniker(
    path: str,
    *,
    namespace: str | None = None,
    revision: int | None = None,
    **params: str,
) -> Moniker:
    """
    Build a Moniker from components.

    Args:
        path: The path string
        namespace: Optional namespace prefix
        revision: Optional revision number
        **params: Query parameters

    Returns:
        Moniker instance
    """
    return Moniker(
        path=parse_path(path),
        namespace=namespace,
        revision=revision,
        params=QueryParams(params) if params else QueryParams({}),
    )
