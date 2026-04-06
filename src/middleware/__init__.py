"""
Middleware package for the MCP server.

FastMCP 3.x provides built-in middleware (e.g., LoggingMiddleware) and supports
custom middleware classes for cross-cutting concerns like authentication, rate
limiting, etc.

Custom middleware should inherit from fastmcp.server.middleware.Middleware and
override specific hook methods (on_call_tool, on_request, etc.).

To add new middleware:
1. Create a new .py file in this directory
2. Import Middleware: from fastmcp.server.middleware import Middleware
3. Define your middleware class inheriting from Middleware
4. Add an instance to the middleware=[] list in create_server() (src/core/server.py)

To remove middleware:
1. Delete the .py file
2. Remove the instance from the middleware=[] list in create_server()
"""
