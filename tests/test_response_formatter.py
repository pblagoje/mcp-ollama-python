"""
Tests for response_formatter.py - Response formatting utilities
"""

import json
import pytest

# Package is installed, import from mcp_ollama_python
from mcp_ollama_python.response_formatter import (
    format_response,
    json_to_markdown,
    array_to_markdown_table,
    _format_object_entry,
    escape_markdown
)
from mcp_ollama_python.models import ResponseFormat


class TestFormatResponse:
    """Tests for format_response function"""

    def test_json_format_valid_json(self):
        """Test JSON format with valid JSON input"""
        input_json = '{"key": "value", "number": 42}'
        result = format_response(input_json, ResponseFormat.JSON)
        assert result == input_json

    def test_json_format_invalid_json(self):
        """Test JSON format with invalid JSON wraps in error"""
        input_text = "This is not JSON"
        result = format_response(input_text, ResponseFormat.JSON)
        parsed = json.loads(result)
        assert "error" in parsed
        assert "Invalid JSON content" in parsed["error"]
        assert parsed["raw_content"] == input_text

    def test_markdown_format_from_json(self):
        """Test markdown format converts JSON to markdown"""
        input_json = '{"name": "test", "value": 123}'
        result = format_response(input_json, ResponseFormat.MARKDOWN)
        assert "**name:**" in result
        assert "**value:**" in result

    def test_markdown_format_plain_text(self):
        """Test markdown format returns plain text as-is"""
        input_text = "Plain text content"
        result = format_response(input_text, ResponseFormat.MARKDOWN)
        assert result == input_text


class TestJsonToMarkdown:
    """Tests for json_to_markdown function"""

    def test_null_value(self):
        """Test null value conversion"""
        result = json_to_markdown(None)
        assert "_null_" in result

    def test_primitive_string(self):
        """Test string primitive conversion"""
        result = json_to_markdown("hello")
        assert "hello" in result

    def test_primitive_number(self):
        """Test number primitive conversion"""
        result = json_to_markdown(42)
        assert "42" in result

    def test_primitive_boolean(self):
        """Test boolean primitive conversion"""
        result = json_to_markdown(True)
        assert "True" in result

    def test_empty_array(self):
        """Test empty array conversion"""
        result = json_to_markdown([])
        assert "_empty array_" in result

    def test_simple_array(self):
        """Test simple array conversion"""
        result = json_to_markdown(["a", "b", "c"])
        assert "- a" in result
        assert "- b" in result
        assert "- c" in result

    def test_empty_object(self):
        """Test empty object conversion"""
        result = json_to_markdown({})
        assert "_empty object_" in result

    def test_simple_object(self):
        """Test simple object conversion"""
        result = json_to_markdown({"key": "value"})
        assert "**key:**" in result
        assert "value" in result

    def test_nested_object(self):
        """Test nested object conversion"""
        data = {
            "outer": {
                "inner": "value"
            }
        }
        result = json_to_markdown(data)
        assert "**outer:**" in result
        assert "**inner:**" in result

    def test_array_of_objects_as_table(self):
        """Test array of objects converts to table"""
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        result = json_to_markdown(data)
        # Should be table format with headers
        assert "|" in result
        assert "---" in result

    def test_underscore_replacement(self):
        """Test underscores in keys are replaced with spaces"""
        result = json_to_markdown({"first_name": "John"})
        assert "**first name:**" in result

    def test_indent_propagation(self):
        """Test indent is properly propagated"""
        result = json_to_markdown({"key": "value"}, indent="  ")
        assert result.startswith("  ")


class TestArrayToMarkdownTable:
    """Tests for array_to_markdown_table function"""

    def test_empty_array(self):
        """Test empty array returns empty array text"""
        result = array_to_markdown_table([])
        assert "_empty array_" in result or result == ""

    def test_non_dict_array(self):
        """Test array of non-dicts falls back"""
        result = array_to_markdown_table(["a", "b"])
        # Should handle gracefully
        assert result is not None

    def test_simple_table(self):
        """Test simple table generation"""
        data = [
            {"col1": "val1", "col2": "val2"},
            {"col1": "val3", "col2": "val4"}
        ]
        result = array_to_markdown_table(data)
        # Check table structure
        lines = result.split("\n")
        assert len(lines) >= 3  # header, separator, at least one row
        assert "|" in lines[0]  # header has pipes
        assert "---" in lines[1]  # separator

    def test_table_with_missing_keys(self):
        """Test table with objects having different keys"""
        data = [
            {"a": 1, "b": 2},
            {"a": 3, "c": 4}  # missing 'b', has 'c'
        ]
        result = array_to_markdown_table(data)
        assert "|" in result

    def test_long_value_truncation(self):
        """Test long values are truncated"""
        long_text = "x" * 100
        data = [{"content": long_text}]
        result = array_to_markdown_table(data)
        assert "..." in result
        assert len(long_text) > len(result.split("|")[1].strip())

    def test_various_value_types(self):
        """Test table handles various value types"""
        data = [
            {"string": "text", "number": 42, "bool": True, "none": None}
        ]
        result = array_to_markdown_table(data)
        assert "|" in result


class TestFormatObjectEntry:
    """Tests for _format_object_entry function"""

    def test_simple_value(self):
        """Test formatting simple key-value"""
        result = _format_object_entry("name", "John", "", set(), 0)
        assert "**name:**" in result
        assert "John" in result

    def test_underscore_key(self):
        """Test underscore replacement in key"""
        result = _format_object_entry("first_name", "Jane", "", set(), 0)
        assert "**first name:**" in result

    def test_nested_dict_value(self):
        """Test formatting with dict value"""
        result = _format_object_entry("details", {"inner": "val"}, "", set(), 0)
        assert "**details:**" in result
        assert "**inner:**" in result

    def test_nested_list_value(self):
        """Test formatting with list value"""
        result = _format_object_entry("items", ["a", "b"], "", set(), 0)
        assert "**items:**" in result

    def test_with_indent(self):
        """Test formatting with indent"""
        result = _format_object_entry("key", "value", "  ", set(), 0)
        assert result.startswith("  ")


class TestIntegration:
    """Integration tests for response formatting"""

    def test_complex_model_list_response(self):
        """Test formatting a complex model list response"""
        data = {
            "models": [
                {
                    "name": "llama3.1:latest",
                    "size": 4661224676,
                    "details": {
                        "family": "llama",
                        "parameter_size": "8B"
                    }
                }
            ]
        }
        json_str = json.dumps(data)

        # Test JSON format
        json_result = format_response(json_str, ResponseFormat.JSON)
        assert json_result == json_str

        # Test markdown format
        md_result = format_response(json_str, ResponseFormat.MARKDOWN)
        assert "**models:**" in md_result

    def test_chat_response_formatting(self):
        """Test formatting a chat response"""
        data = {
            "model": "llama3.1",
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you?"
            },
            "done": True
        }
        json_str = json.dumps(data)

        md_result = format_response(json_str, ResponseFormat.MARKDOWN)
        assert "**model:**" in md_result
        assert "**message:**" in md_result

    def test_error_response_formatting(self):
        """Test formatting an error response"""
        data = {
            "error": "Model not found",
            "status_code": 404
        }
        json_str = json.dumps(data)

        md_result = format_response(json_str, ResponseFormat.MARKDOWN)
        assert "**error:**" in md_result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
