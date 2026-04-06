"""MCP server bootstrap: creates FastMCP with providers, middleware, and auth."""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.middleware.logging import LoggingMiddleware
from fastmcp.server.providers import FileSystemProvider

from src.core.auth import configure_auth
from src.core.logging import configure_logging, get_logger

log = get_logger("bootstrap")

SRC_ROOT = Path(__file__).resolve().parent.parent


def create_server() -> FastMCP:
    """Create and configure the FastMCP server instance."""
    load_dotenv(override=True)
    configure_logging(os.getenv("MCP_LOG_LEVEL", "INFO"))

    name = os.getenv("MCP_SERVER_NAME", "fastmcp-unified")
    hot_reload = os.getenv("MCP_HOT_RELOAD", "0").lower() in {"1", "true", "yes"}

    providers = [
        FileSystemProvider(SRC_ROOT / "tools", reload=hot_reload),
        FileSystemProvider(SRC_ROOT / "resources", reload=hot_reload),
        FileSystemProvider(SRC_ROOT / "prompts", reload=hot_reload),
    ]

    middleware = [LoggingMiddleware()]
    auth = configure_auth()

    mcp = FastMCP(
        name,
        providers=providers,
        middleware=middleware,
        auth=auth,
    )

    return mcp


def run_server(mcp: FastMCP) -> None:
    """Run the server with the configured transport."""
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()

    if transport == "http":
        host = os.getenv("MCP_HTTP_HOST", "127.0.0.1")
        port = int(os.getenv("MCP_HTTP_PORT", "8000"))
        path = os.getenv("MCP_HTTP_PATH", "/mcp/")
        log.info(f"Starting FastMCP HTTP server at http://{host}:{port}{path}")
        mcp.run(transport="http", host=host, port=port, path=path)
    else:
        log.info("Starting FastMCP in STDIO mode")
        mcp.run(transport="stdio")
