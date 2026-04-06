"""
End-to-end integration tests for MCP server startup and component discovery.

Tests that the server correctly discovers tools, resources, and prompts via
FileSystemProvider, and that discovered components behave correctly at runtime.
"""

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from fastmcp.utilities.tests import run_server_async

from src.core.server import create_server


@pytest.fixture
async def client():
    """Shared in-process client wrapping a freshly created server."""
    mcp = create_server()
    async with Client(mcp) as c:
        yield c


# ---------------------------------------------------------------------------
# Discovery tests
# ---------------------------------------------------------------------------

EXPECTED_TOOLS = [
    "echo",
    "delete_all",
    "get_weather",
    "write_release_notes",
    "process_data",
    "validate_input",
    "analyze_text",
    "configure_system",
    "calculate_statistics",
    "format_text",
]

EXPECTED_RESOURCES = [
    "readme_snippet",
    "japan_profile",
    "passport_lost_protocol",
    "first_international_trip_checklist",
]

EXPECTED_PROMPTS = [
    "summarize",
    "classify",
    "analyze_sentiment",
    "extract_entities",
    "generate_docstring",
    "generate_readme",
    "explain_code",
    "generate_api_docs",
    "translate_text",
    "proofread_text",
    "compare_texts",
    "generate_title",
]


@pytest.mark.parametrize("tool_name", EXPECTED_TOOLS)
async def test_server_discovers_tools(client, tool_name):
    """Server discovers all expected tools via FileSystemProvider."""
    tools = await client.list_tools()
    names = {t.name for t in tools}
    assert tool_name in names, f"Expected tool '{tool_name}' not found in {sorted(names)}"


@pytest.mark.parametrize("resource_name", EXPECTED_RESOURCES)
async def test_server_discovers_resources(client, resource_name):
    """Server discovers all expected resources via FileSystemProvider."""
    resources = await client.list_resources()
    names = {r.name for r in resources}
    assert resource_name in names, (
        f"Expected resource '{resource_name}' not found in {sorted(names)}"
    )


@pytest.mark.parametrize("prompt_name", EXPECTED_PROMPTS)
async def test_server_discovers_prompts(client, prompt_name):
    """Server discovers all expected prompts via FileSystemProvider."""
    prompts = await client.list_prompts()
    names = {p.name for p in prompts}
    assert prompt_name in names, (
        f"Expected prompt '{prompt_name}' not found in {sorted(names)}"
    )


# ---------------------------------------------------------------------------
# Tool behaviour tests
# ---------------------------------------------------------------------------


async def test_echo_tool_roundtrip(client):
    """echo tool returns the exact message it receives."""
    message = "hello from e2e test"
    result = await client.call_tool("echo", {"message": message})
    assert not result.is_error, f"echo returned an error: {result}"
    assert result.data == message, (
        f"Expected '{message}', got '{result.data}'"
    )


async def test_tool_error_handling(client):
    """validate_input raises ToolError for empty/whitespace input.

    FastMCP's Client raises ToolError directly (raise_on_error=True by default)
    rather than returning an error result object.
    """
    with pytest.raises(ToolError, match="empty or whitespace"):
        await client.call_tool("validate_input", {"data": "   "})


async def test_format_text_uppercase(client):
    """format_text applies uppercase transformation correctly."""
    result = await client.call_tool(
        "format_text", {"text": "  hello world  ", "uppercase": True, "trim": True}
    )
    assert not result.is_error, f"format_text returned an error: {result}"
    assert result.data == "HELLO WORLD", (
        f"Expected 'HELLO WORLD', got '{result.data}'"
    )


async def test_configure_system_returns_dict(client):
    """configure_system returns a config dict with expected keys."""
    result = await client.call_tool(
        "configure_system", {"setting": "medium", "timeout": 60}
    )
    assert not result.is_error, f"configure_system returned an error: {result}"
    config = result.data
    assert isinstance(config, dict), f"Expected dict, got {type(config)}"
    assert config.get("setting") == "medium", f"Unexpected config: {config}"
    assert config.get("status") == "configured", f"Unexpected config: {config}"


# ---------------------------------------------------------------------------
# Resource read test
# ---------------------------------------------------------------------------


async def test_resource_read_readme_snippet(client):
    """readme_snippet resource returns non-empty string content."""
    content = await client.read_resource("resource://readme-snippet")
    assert content, "Expected non-empty content from readme_snippet resource"
    text = content[0].text if isinstance(content, list) else str(content)
    assert len(text) > 0, f"readme_snippet content was empty: {text!r}"


async def test_analyze_text_structured_output(client):
    """analyze_text returns structured AnalysisResult with expected fields."""
    result = await client.call_tool(
        "analyze_text", {"text": "Hello world. This is a test sentence."}
    )
    assert not result.is_error, f"analyze_text returned an error: {result}"
    data = result.data
    for attr in ("word_count", "character_count", "sentence_count",
                 "avg_word_length", "unique_words"):
        assert hasattr(data, attr), f"Missing attribute '{attr}' in result: {data}"
    assert data.word_count > 0, f"Expected positive word_count: {data}"


# ---------------------------------------------------------------------------
# HTTP transport test
# ---------------------------------------------------------------------------


async def test_http_transport_lists_tools():
    """Server starts on HTTP transport and responds to tool listing."""
    mcp = create_server()
    async with run_server_async(mcp, transport="streamable-http") as url:
        async with Client(url) as http_client:
            tools = await http_client.list_tools()
            names = {t.name for t in tools}
            assert "echo" in names, f"echo not found via HTTP transport: {sorted(names)}"
            assert len(tools) >= len(EXPECTED_TOOLS), (
                f"HTTP transport discovered only {len(tools)} tools, "
                f"expected at least {len(EXPECTED_TOOLS)}"
            )
