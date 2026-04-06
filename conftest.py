"""Pytest configuration for MCP server projects.

This file is placed at the project root to ensure src.* imports resolve
correctly.  The project uses ``src.`` prefixed absolute imports throughout
(e.g., ``from src.core.server import create_server``), so the *project root*
must be on sys.path rather than the ``src/`` directory itself.
"""

import sys
from pathlib import Path

project_root = str(Path(__file__).parent)

if project_root not in sys.path:
    sys.path.insert(0, project_root)
