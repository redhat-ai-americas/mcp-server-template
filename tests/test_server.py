"""Tests for server creation and configuration."""

import os
from unittest.mock import patch

from fastmcp import FastMCP

from src.core.server import create_server


def test_create_server_returns_fastmcp():
    """create_server() returns a configured FastMCP instance."""
    mcp = create_server()
    assert isinstance(mcp, FastMCP)


def test_create_server_uses_env_name():
    """Server name comes from MCP_SERVER_NAME env var."""
    with patch.dict(os.environ, {"MCP_SERVER_NAME": "test-server"}):
        mcp = create_server()
        assert mcp.name == "test-server"
