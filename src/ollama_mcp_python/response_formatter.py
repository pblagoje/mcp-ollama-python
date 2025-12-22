"""
Response formatting utilities
"""

import json
from typing import Any, Dict, List
from .models import ResponseFormat


def format_response(content: Any, format: ResponseFormat) -> str:
    """Format response content based on the specified format"""
    # Handle dict/list input - convert to JSON string first
    if isinstance(content, (dict, list)):
        if format == ResponseFormat.JSON:
            return json.dumps(content, indent=2)
        else:
            # Format as markdown
            return json_to_markdown(content)
    
    # Handle string input
    if format == ResponseFormat.JSON:
        # For JSON format, validate and potentially wrap errors
        try:
            # Try to parse to validate it's valid JSON
            json.loads(content)
            return content
        except json.JSONDecodeError:
            # If not valid JSON, wrap in error object
            return json.dumps({
                "error": "Invalid JSON content",
                "raw_content": content,
            })

    # Format as markdown
    try:
        data = json.loads(content)
        return json_to_markdown(data)
    except json.JSONDecodeError:
        # If not valid JSON, return as-is
        return content


def json_to_markdown(data: Any, indent: str = "") -> str:
    """Convert JSON data to markdown format"""
    # Handle null/undefined
    if data is None:
        return f"{indent}_null_"

    # Handle primitives
    if not isinstance(data, (dict, list)):
        return f"{indent}{str(data)}"

    # Handle arrays
    if isinstance(data, list):
        if len(data) == 0:
            return f"{indent}_empty array_"

        # Check if array of objects with consistent keys (table format)
        if len(data) > 0 and isinstance(data[0], dict) and data[0] is not None:
            return array_to_markdown_table(data, indent)

        # Array of primitives or mixed types
        return "\n".join(
            f"{indent}- {json_to_markdown(item, '')}"
            for item in data
        )

    # Handle objects
    entries = list(data.items())
    if len(entries) == 0:
        return f"{indent}_empty object_"

    return "\n".join(
        _format_object_entry(key, value, indent)
        for key, value in entries
    )


def _format_object_entry(key: str, value: Any, indent: str) -> str:
    """Format a single key-value pair in an object"""
    formatted_key = key.replace("_", " ")
    if isinstance(value, (dict, list)) and value is not None:
        if isinstance(value, list):
            return f"{indent}**{formatted_key}:**\n{json_to_markdown(value, indent + '  ')}"
        return f"{indent}**{formatted_key}:**\n{json_to_markdown(value, indent + '  ')}"
    return f"{indent}**{formatted_key}:** {value}"


def array_to_markdown_table(data: List[Dict[str, Any]], indent: str = "") -> str:
    """Convert array of objects to markdown table format"""
    if not data or not isinstance(data[0], dict):
        return json_to_markdown(data, indent)

    # Get all unique keys from all objects
    all_keys = set()
    for item in data:
        if isinstance(item, dict):
            all_keys.update(item.keys())

    if not all_keys:
        return f"{indent}_empty array_"

    headers = list(all_keys)
    rows = []

    # Add header row
    header_row = "| " + " | ".join(headers) + " |"
    separator_row = "|" + "|".join("---" for _ in headers) + "|"
    rows.extend([header_row, separator_row])

    # Add data rows
    for item in data:
        if isinstance(item, dict):
            row_values = []
            for header in headers:
                value = item.get(header, "")
                # Truncate long values for table display
                if isinstance(value, str) and len(value) > 50:
                    value = value[:47] + "..."
                row_values.append(str(value))
            rows.append("| " + " | ".join(row_values) + " |")

    return "\n".join(rows)
