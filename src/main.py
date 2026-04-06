#!/usr/bin/env python3
"""Entry point for the MCP server."""

from src.core.server import create_server, run_server


def main() -> None:
    mcp = create_server()
    run_server(mcp)


if __name__ == "__main__":
    main()
