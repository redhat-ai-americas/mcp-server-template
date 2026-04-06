"""Tests for authentication configuration."""

import os
from unittest.mock import patch

from src.core.auth import configure_auth


def test_auth_disabled_when_no_env():
    """Auth is None when MCP_AUTH_JWT_ALG is not set."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("MCP_AUTH")}
    with patch.dict(os.environ, env, clear=True):
        auth = configure_auth()
        assert auth is None


def test_auth_disabled_when_alg_but_no_key():
    """Auth is None when algorithm set but no key/secret."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("MCP_AUTH")}
    env["MCP_AUTH_JWT_ALG"] = "HS256"
    with patch.dict(os.environ, env, clear=True):
        auth = configure_auth()
        assert auth is None


def test_auth_enabled_with_secret():
    """Auth returns a verifier when algorithm and secret are set."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("MCP_AUTH")}
    env["MCP_AUTH_JWT_ALG"] = "HS256"
    env["MCP_AUTH_JWT_SECRET"] = "test-secret-key"
    with patch.dict(os.environ, env, clear=True):
        auth = configure_auth()
        assert auth is not None
