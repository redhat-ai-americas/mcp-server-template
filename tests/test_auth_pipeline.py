"""Integration tests for the JWT authentication pipeline.

Tests the full auth stack from token validation through per-component scope checks:
- JWTVerifier validates bearer tokens over HTTP (HS256 shared secret)
- require_scopes("admin") enforces per-tool scope checks
- In-memory (STDIO) transport skips auth; HTTP transport enforces it

These tests spin up a real HTTP server using run_server_async so that the Bearer
auth middleware is active. The in-process (FastMCPTransport) bypasses auth
because it runs over STDIO, which is intentional FastMCP behaviour.
"""

import time

import httpx
import pytest
from authlib.jose import JsonWebToken
from fastmcp import Client, FastMCP
from fastmcp.client.auth.bearer import BearerAuth
from fastmcp.exceptions import ToolError
from fastmcp.server.auth import require_scopes
from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.utilities.tests import run_server_async

# ---------------------------------------------------------------------------
# Test constants
# ---------------------------------------------------------------------------

TEST_SECRET = "test-secret-key-for-hs256-do-not-use-in-production"
TEST_ISSUER = "test-auth-server"


# ---------------------------------------------------------------------------
# JWT token factory
# ---------------------------------------------------------------------------


def make_token(scopes: list[str], *, expired: bool = False) -> str:
    """Generate a signed HS256 JWT with the given scopes.

    Uses authlib directly (already a fastmcp dependency) so we don't need to
    add pyjwt as a separate test dependency.
    """
    now = int(time.time())
    exp = now - 60 if expired else now + 3600
    payload = {
        "sub": "test-user",
        "iss": TEST_ISSUER,
        "iat": now,
        "exp": exp,
        "scope": " ".join(scopes),
    }
    jwt = JsonWebToken(["HS256"])
    token_bytes = jwt.encode({"alg": "HS256"}, payload, TEST_SECRET)
    return token_bytes.decode("utf-8")


# ---------------------------------------------------------------------------
# Server factory
# ---------------------------------------------------------------------------


def build_auth_server() -> FastMCP:
    """Build a minimal FastMCP server with HS256 JWT auth and an admin-scoped tool.

    Uses @mcp.tool() instance decoration deliberately for test isolation — this
    avoids FileSystemProvider and keeps the test self-contained. The CLAUDE.md
    prohibition on @mcp.tool applies to src/ component files, not test helpers.
    """
    verifier = JWTVerifier(
        public_key=TEST_SECRET,
        algorithm="HS256",
        issuer=TEST_ISSUER,
    )
    mcp = FastMCP("auth-test-server", auth=verifier)

    @mcp.tool(auth=require_scopes("admin"))
    def admin_action() -> str:
        """A tool that requires the 'admin' scope."""
        return "admin action completed"

    return mcp


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def server_url():
    """Run the auth-protected server over HTTP and yield its URL."""
    mcp = build_auth_server()
    async with run_server_async(mcp, transport="streamable-http") as url:
        yield url


# ---------------------------------------------------------------------------
# Scenario 1: No token — server returns 401 before the MCP handshake
# ---------------------------------------------------------------------------


async def test_unauthenticated_request_is_rejected(server_url: str):
    """A request without a bearer token receives HTTP 401.

    The JWTVerifier-backed BearerAuthBackend rejects the connection before
    any MCP message is processed.
    """
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        async with Client(server_url) as client:
            await client.list_tools()

    assert exc_info.value.response.status_code == 401, (
        f"Expected 401 Unauthorized, got {exc_info.value.response.status_code}"
    )


# ---------------------------------------------------------------------------
# Scenario 2: Valid token with correct scope — tool call succeeds
# ---------------------------------------------------------------------------


async def test_admin_token_can_call_admin_tool(server_url: str):
    """A valid JWT with scope='admin' successfully calls the admin-scoped tool."""
    token = make_token(scopes=["admin"])

    async with Client(server_url, auth=BearerAuth(token)) as client:
        result = await client.call_tool("admin_action", {})

    assert not result.is_error, f"Unexpected error from admin_action: {result}"
    assert result.data == "admin action completed", (
        f"Unexpected result: {result.data!r}"
    )


# ---------------------------------------------------------------------------
# Scenario 3: Valid token with wrong scope — tool is hidden, call raises ToolError
# ---------------------------------------------------------------------------


async def test_wrong_scope_token_cannot_call_admin_tool(server_url: str):
    """A valid JWT with scope='read' (not 'admin') cannot invoke the admin tool.

    The server hides the tool from list_tools and raises a ToolError (isError=True
    result with "Unknown tool") when it is called directly, because FastMCP hides
    unauthorised tools rather than returning a protocol-level error.
    """
    token = make_token(scopes=["read"])

    async with Client(server_url, auth=BearerAuth(token)) as client:
        # The tool should not be visible to this token.
        tools = await client.list_tools()
        names = {t.name for t in tools}
        assert "admin_action" not in names, (
            f"admin_action should be hidden from read-scoped token, "
            f"but was visible in: {sorted(names)}"
        )

        # Calling it directly must be rejected. FastMCP surfaces this as a
        # ToolError (isError=True result) with "Unknown tool" because the server
        # hides unauthorised tools rather than raising a protocol-level error.
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("admin_action", {})

    error_message = str(exc_info.value)
    assert "admin_action" in error_message, (
        f"Expected tool name in error message, got: {error_message!r}"
    )
