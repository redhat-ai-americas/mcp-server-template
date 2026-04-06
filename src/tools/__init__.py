"""
Tools package for the MCP server.

Tool modules are automatically discovered by FileSystemProvider at startup.

To add a new tool:
1. Create a new .py file in this directory
2. Import the standalone decorator: from fastmcp.tools import tool
3. Define your tool function with @tool decorator
4. FileSystemProvider will automatically discover and register it

To remove a tool:
1. Simply delete the .py file
"""
