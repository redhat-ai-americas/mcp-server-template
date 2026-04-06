"""Integration tests for Jinja2 generator templates in .fips-agents-cli/generators/.

Validates that each component template:
- Renders without errors given representative variables
- Produces valid Python (ast.parse passes)
- Contains expected FastMCP 3.x import/decorator patterns
- Does not contain FastMCP 2.x anti-patterns
"""

import ast
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined

# ---------------------------------------------------------------------------
# Template loading helpers
# ---------------------------------------------------------------------------

GENERATORS_ROOT = (
    Path(__file__).parent.parent / ".fips-agents-cli" / "generators"
)

V2_ANTI_PATTERNS = [
    "from src.core.app import mcp",
    "@mcp.tool",
    "@mcp.resource",
    "@mcp.prompt",
]


def _render_template(template_subpath: str, variables: dict) -> str:
    """Load a Jinja2 template relative to GENERATORS_ROOT and render it."""
    template_path = GENERATORS_ROOT / template_subpath
    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )
    template = env.get_template(template_path.name)
    return template.render(**variables)


def _assert_valid_python(source: str, label: str) -> None:
    try:
        ast.parse(source)
    except SyntaxError as exc:
        # Include the rendered source in the error for easy debugging
        raise AssertionError(
            f"Template '{label}' rendered invalid Python.\n"
            f"SyntaxError: {exc}\n\n--- Rendered output ---\n{source}"
        ) from exc


def _assert_no_v2_patterns(source: str, label: str) -> None:
    for pattern in V2_ANTI_PATTERNS:
        assert pattern not in source, (
            f"Template '{label}' contains v2.x anti-pattern: {pattern!r}\n"
            f"--- Rendered output ---\n{source}"
        )


# ---------------------------------------------------------------------------
# Tool template
# ---------------------------------------------------------------------------

TOOL_VARS_BASIC = {
    "description": "Test tool for validation",
    "component_name": "test_tool",
    "params": [
        {
            "name": "input_text",
            "type": "str",
            "description": "The input text",
            "min_length": None,
            "max_length": None,
        },
    ],
    "async": True,
    "with_context": True,
    "with_auth": False,
    "return_type": "str",
    "read_only": True,
    "idempotent": True,
    "open_world": False,
}

TOOL_VARS_WITH_AUTH = {
    **TOOL_VARS_BASIC,
    "with_auth": True,
    "required_scopes": ["admin"],
}


@pytest.mark.parametrize(
    "label, variables, expected_v3_patterns, extra_absent",
    [
        (
            "tool_basic",
            TOOL_VARS_BASIC,
            [
                "from fastmcp.tools import tool",
                "@tool(",
            ],
            ["require_scopes"],
        ),
        (
            "tool_with_auth",
            TOOL_VARS_WITH_AUTH,
            [
                "from fastmcp.tools import tool",
                "@tool(",
                "from fastmcp.server.auth import require_scopes",
            ],
            [],
        ),
    ],
)
def test_tool_template(label, variables, expected_v3_patterns, extra_absent):
    source = _render_template("tool/component.py.j2", variables)
    _assert_valid_python(source, label)
    _assert_no_v2_patterns(source, label)
    for pattern in expected_v3_patterns:
        assert pattern in source, (
            f"[{label}] Expected v3.x pattern not found: {pattern!r}\n"
            f"--- Rendered output ---\n{source}"
        )
    for pattern in extra_absent:
        assert pattern not in source, (
            f"[{label}] Pattern should be absent but was found: {pattern!r}\n"
            f"--- Rendered output ---\n{source}"
        )


# ---------------------------------------------------------------------------
# Resource template
# ---------------------------------------------------------------------------

RESOURCE_VARS = {
    "description": "Test resource for validation",
    "component_name": "test_resource",
    "uri": "resource://test-resource",
    "params": [],
    "async": False,
    "mime_type": "application/json",
}


def test_resource_template():
    source = _render_template("resource/component.py.j2", RESOURCE_VARS)
    _assert_valid_python(source, "resource")
    _assert_no_v2_patterns(source, "resource")
    for pattern in ["from fastmcp.resources import resource", "@resource("]:
        assert pattern in source, (
            f"[resource] Expected v3.x pattern not found: {pattern!r}\n"
            f"--- Rendered output ---\n{source}"
        )


# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

PROMPT_VARS = {
    "description": "Test prompt for validation",
    "component_name": "test_prompt",
    "params": [
        {
            "name": "query",
            "type_hint": "str",
            "description": "User query",
            "optional": False,
        }
    ],
    "async": False,
    "with_context": False,
    "return_type": "str",
    "prompt_name": None,
    "title": None,
    "tags": None,
    "meta": None,
    "needs_prompt_imports": False,
    "with_schema": False,
    "prompt_instruction": "Analyze the following:",
}


def test_prompt_template():
    source = _render_template("prompt/component.py.j2", PROMPT_VARS)
    _assert_valid_python(source, "prompt")
    _assert_no_v2_patterns(source, "prompt")
    for pattern in ["from fastmcp.prompts import prompt", "@prompt"]:
        assert pattern in source, (
            f"[prompt] Expected v3.x pattern not found: {pattern!r}\n"
            f"--- Rendered output ---\n{source}"
        )


# ---------------------------------------------------------------------------
# Middleware template
# ---------------------------------------------------------------------------

MIDDLEWARE_VARS = {
    "description": "Test middleware for validation",
    "component_name": "test_middleware",
}


def test_middleware_template():
    source = _render_template("middleware/component.py.j2", MIDDLEWARE_VARS)
    _assert_valid_python(source, "middleware")
    _assert_no_v2_patterns(source, "middleware")
    for pattern in [
        "from fastmcp.server.middleware import",
        "(Middleware):",
    ]:
        assert pattern in source, (
            f"[middleware] Expected v3.x pattern not found: {pattern!r}\n"
            f"--- Rendered output ---\n{source}"
        )
    # Confirm class-based approach (not function-based)
    assert "class " in source, (
        f"[middleware] Expected class-based middleware definition\n"
        f"--- Rendered output ---\n{source}"
    )
