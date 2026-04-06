"""Tests for prompt module structure and conventions.

Validates that prompt files follow FastMCP 3.x standalone decorator patterns.
Uses AST inspection rather than runtime imports because the prompt modules
depend on FastMCP standalone decorators whose exact API may still be in flux.
"""

import ast
from pathlib import Path

import pytest


PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "prompts" / "examples"


def _parse_module(filename: str) -> ast.Module:
    """Parse a prompt module into an AST."""
    path = PROMPTS_DIR / filename
    assert path.exists(), f"{filename} should exist in {PROMPTS_DIR}"
    return ast.parse(path.read_text())


def _get_decorated_functions(tree: ast.Module) -> list[ast.FunctionDef]:
    """Return all top-level functions that have a decorator."""
    return [
        node
        for node in ast.iter_child_nodes(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.decorator_list
    ]


def _uses_prompt_decorator(func: ast.FunctionDef) -> bool:
    """Check if function uses @prompt or @prompt() decorator."""
    for dec in func.decorator_list:
        # @prompt (bare name)
        if isinstance(dec, ast.Name) and dec.id == "prompt":
            return True
        # @prompt() (call)
        if isinstance(dec, ast.Call):
            if isinstance(dec.func, ast.Name) and dec.func.id == "prompt":
                return True
    return False


def _has_return_type(func: ast.FunctionDef) -> bool:
    """Check if function has a return type annotation."""
    return func.returns is not None


# -- analysis.py --

class TestAnalysisPrompts:
    """Verify analysis.py prompt structure."""

    @pytest.fixture(autouse=True)
    def _parse(self):
        self.tree = _parse_module("analysis.py")
        self.functions = _get_decorated_functions(self.tree)

    def test_expected_prompts_exist(self):
        names = {f.name for f in self.functions}
        for expected in ("summarize", "classify", "analyze_sentiment", "extract_entities"):
            assert expected in names, f"analysis.py should define '{expected}' prompt"

    def test_all_use_prompt_decorator(self):
        for func in self.functions:
            assert _uses_prompt_decorator(func), (
                f"{func.name} should use the @prompt decorator"
            )

    def test_all_have_return_type(self):
        for func in self.functions:
            assert _has_return_type(func), (
                f"{func.name} should have a return type annotation"
            )

    def test_all_have_docstrings(self):
        for func in self.functions:
            docstring = ast.get_docstring(func)
            assert docstring, f"{func.name} should have a docstring"

    def test_imports_standalone_prompt(self):
        """Module imports prompt from fastmcp.prompts (standalone decorator)."""
        source = (PROMPTS_DIR / "analysis.py").read_text()
        assert "from fastmcp.prompts import prompt" in source


# -- documentation.py --

class TestDocumentationPrompts:
    """Verify documentation.py prompt structure."""

    @pytest.fixture(autouse=True)
    def _parse(self):
        self.tree = _parse_module("documentation.py")
        self.functions = _get_decorated_functions(self.tree)

    def test_expected_prompts_exist(self):
        names = {f.name for f in self.functions}
        for expected in ("generate_docstring", "generate_readme", "explain_code", "generate_api_docs"):
            assert expected in names, f"documentation.py should define '{expected}' prompt"

    def test_all_use_prompt_decorator(self):
        for func in self.functions:
            assert _uses_prompt_decorator(func), (
                f"{func.name} should use the @prompt decorator"
            )

    def test_all_have_return_type(self):
        for func in self.functions:
            assert _has_return_type(func), (
                f"{func.name} should have a return type annotation"
            )

    def test_imports_standalone_prompt(self):
        source = (PROMPTS_DIR / "documentation.py").read_text()
        assert "from fastmcp.prompts import prompt" in source


# -- general.py --

class TestGeneralPrompts:
    """Verify general.py prompt structure."""

    @pytest.fixture(autouse=True)
    def _parse(self):
        self.tree = _parse_module("general.py")
        self.functions = _get_decorated_functions(self.tree)

    def test_expected_prompts_exist(self):
        names = {f.name for f in self.functions}
        for expected in ("translate_text", "proofread_text", "compare_texts", "generate_title"):
            assert expected in names, f"general.py should define '{expected}' prompt"

    def test_all_use_prompt_decorator(self):
        for func in self.functions:
            assert _uses_prompt_decorator(func), (
                f"{func.name} should use the @prompt decorator"
            )

    def test_all_have_return_type(self):
        for func in self.functions:
            assert _has_return_type(func), (
                f"{func.name} should have a return type annotation"
            )

    def test_imports_standalone_prompt(self):
        source = (PROMPTS_DIR / "general.py").read_text()
        assert "from fastmcp.prompts import prompt" in source
