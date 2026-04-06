"""
Prompts package for the MCP server.

Prompt modules are automatically discovered by FileSystemProvider at startup.

To add a new prompt:
1. Create a new .py file in this directory
2. Import the standalone decorator: from fastmcp.prompts import prompt
3. Define your prompt function with @prompt decorator
4. FileSystemProvider will automatically discover and register it

To remove a prompt:
1. Simply delete the .py file
"""
