"""Shared MCP server instance.

In FastMCP 3.x, components use standalone decorators (@tool, @resource, @prompt)
and are discovered by FileSystemProvider. This module provides create_server()
for cases where direct access to the FastMCP instance is needed (e.g., tests).
"""

from src.core.server import create_server

__all__ = ["create_server"]
