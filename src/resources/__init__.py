"""
Resources package for the MCP server.

Resource modules are automatically discovered by FileSystemProvider at startup.

To add a new resource:
1. Create a new .py file in this directory or any subdirectory
   Example: resources/country_profiles/japan.py
2. Import the standalone decorator: from fastmcp.resources import resource
3. Define your resource function with @resource("uri://...") decorator
4. FileSystemProvider will automatically discover and register it

To remove a resource:
1. Simply delete the .py file

Subdirectories are supported and encouraged for organizing related resources.
Examples:
- resources/country_profiles/japan.py
- resources/checklists/first_international_trip.py
- resources/emergency_protocols/passport_lost.py
"""
