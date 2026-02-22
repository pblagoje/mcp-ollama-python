"""
Response formatting utilities
"""

import json
import logging
from typing import Any, Dict, List, Set, Optional

try:
    from mcp_ollama_python.models import ResponseFormat
except ImportError:
    from .models import ResponseFormat

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MAX_RECURSION_DEPTH = 100
MAX_TABLE_CELL_LENGTH = 50


def format_response(content: Any, format: ResponseFormat) -> str:
    """
    Format response content based on the specified format.

    Args:
        content: Content to format (dict, list, or string)
        format: Desired output format (JSON or MARKDOWN)

    Returns:
        Formatted string

    Raises:
        ValueError: If format is not a valid ResponseFormat
    """
    # Validate format parameter
    if format not in [ResponseFormat.JSON, ResponseFormat.MARKDOWN]:
        raise ValueError(f"Unsupported format: {format}")

    # Handle dict/list input
    if isinstance(content, (dict, list)):
        if format == ResponseFormat.JSON:
            try:
                return json.dumps(content, indent=2)
            except (TypeError, ValueError) as e:
                logger.error(f"Failed to serialize content to JSON: {e}")
                return json.dumps(
                    {"error": "Failed to serialize content", "details": str(e)}
                )
        else:
            # Format as markdown
            return json_to_markdown(content)

    # Handle string input
    if isinstance(content, str):
        if format == ResponseFormat.JSON:
            # For JSON format, validate and potentially wrap errors
            try:
                # Try to parse to validate it's valid JSON
                json.loads(content)
                return content
            except json.JSONDecodeError as e:
                # If not valid JSON, wrap in error object
                logger.warning(f"Invalid JSON content: {e}")
                return json.dumps(
                    {
                        "error": "Invalid JSON content",
                        "raw_content": content,
                    }
                )
        else:
            # Format as markdown
            try:
                data = json.loads(content)
                return json_to_markdown(data)
            except json.JSONDecodeError:
                # If not valid JSON, return as-is (it's plain text)
                return content

    # Handle other types (int, float, bool, None)
    if format == ResponseFormat.JSON:
        return json.dumps(content)
    else:
        return str(content)


def json_to_markdown(
    data: Any, indent: str = "", seen: Optional[Set[int]] = None, depth: int = 0
) -> str:
    """
    Convert JSON data to markdown format.

    Args:
        data: Data to convert (dict, list, primitive, or None)
        indent: Indentation string for nested elements
        seen: Set of object IDs to detect circular references
        depth: Current recursion depth

    Returns:
        Markdown-formatted string

    Note:
        Circular references are handled gracefully by returning a placeholder.
        Maximum recursion depth is enforced to prevent stack overflow.
    """
    # Initialize seen set on first call
    if seen is None:
        seen = set()

    # Check recursion depth
    if depth > MAX_RECURSION_DEPTH:
        logger.warning(f"Maximum recursion depth ({MAX_RECURSION_DEPTH}) exceeded")
        return f"{indent}_max depth exceeded_"

    # Handle null/undefined
    if data is None:
        return f"{indent}_null_"

    # Handle primitives
    if not isinstance(data, (dict, list)):
        return f"{indent}{escape_markdown(str(data))}"

    # Check for circular references
    data_id = id(data)
    if data_id in seen:
        return f"{indent}_circular reference_"

    # Add to seen set (keep it there to detect all references, not just circular ones)
    seen.add(data_id)

    try:
        # Handle arrays
        if isinstance(data, list):
            if len(data) == 0:
                return f"{indent}_empty array_"

            # Check if array of objects with consistent keys (table format)
            if isinstance(data[0], dict) and data[0] is not None:
                return array_to_markdown_table(data, indent, seen, depth)

            # Array of primitives or mixed types
            return "\n".join(
                f"{indent}- {json_to_markdown(item, '', seen, depth + 1)}"
                for item in data
            )

        # Handle objects
        entries = list(data.items())
        if len(entries) == 0:
            return f"{indent}_empty object_"

        return "\n".join(
            _format_object_entry(key, value, indent, seen, depth)
            for key, value in entries
        )
    finally:
        # Do not remove from seen set after processing
        pass


def escape_markdown(text: str) -> str:
    """
    Escape special Markdown characters to prevent formatting issues.

    Args:
        text: Text to escape

    Returns:
        Escaped text safe for Markdown rendering
    """
    if not isinstance(text, str):
        return str(text)

    # Escape backslash first to prevent double-escaping
    text = text.replace("\\", "\\\\")

    # Escape other Markdown special characters
    for char in ["|", "*", "_", "`", "[", "]", "#"]:
        text = text.replace(char, f"\\{char}")

    return text


def _format_object_entry(
    key: str, value: Any, indent: str, seen: Set[int], depth: int
) -> str:
    """
    Format a single key-value pair in an object.

    Args:
        key: Object key
        value: Object value
        indent: Current indentation
        seen: Set of seen object IDs
        depth: Current recursion depth

    Returns:
        Formatted key-value pair
    """
    formatted_key = escape_markdown(key.replace("_", " "))
    if isinstance(value, (dict, list)) and value is not None:
        return f"{indent}**{formatted_key}:**\n{json_to_markdown(value, indent + '  ', seen, depth + 1)}"
    return f"{indent}**{formatted_key}:** {escape_markdown(str(value))}"


def array_to_markdown_table(
    data: List[Dict[str, Any]],
    indent: str = "",
    seen: Optional[Set[int]] = None,
    depth: int = 0,
) -> str:
    """
    Convert array of objects to markdown table format.

    Args:
        data: List of dictionaries to convert
        indent: Indentation string
        seen: Set of seen object IDs
        depth: Current recursion depth

    Returns:
        Markdown table string
    """
    if not data or not isinstance(data[0], dict):
        return json_to_markdown(data, indent, seen, depth)

    # Get all unique keys from all objects, preserving insertion order
    all_keys = dict.fromkeys(
        key for item in data if isinstance(item, dict) for key in item
    )

    if not all_keys:
        return f"{indent}_empty array_"

    headers = [escape_markdown(str(h)) for h in all_keys]
    rows = []

    # Add header row
    header_row = "| " + " | ".join(headers) + " |"
    separator_row = "|" + "|".join("---" for _ in headers) + "|"
    rows.extend([header_row, separator_row])

    # Add data rows
    for item in data:
        if isinstance(item, dict):
            row_values = []
            for header in all_keys:
                value = item.get(header, "")
                value_str = str(value)

                # Truncate long values for table display
                if len(value_str) > MAX_TABLE_CELL_LENGTH:
                    value_str = value_str[: MAX_TABLE_CELL_LENGTH - 3] + "..."

                # Escape markdown characters
                row_values.append(escape_markdown(value_str))
            rows.append("| " + " | ".join(row_values) + " |")

    return "\n".join(rows)
