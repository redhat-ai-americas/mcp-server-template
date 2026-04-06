"""Authentication configuration using FastMCP's built-in auth system.

FastMCP 3.x provides JWTVerifier for token validation and RemoteAuthProvider
for OAuth 2.0 Protected Resource metadata. Per-component scope checks use
the `auth=require_scopes(...)` parameter on @tool/@resource/@prompt decorators.

Environment variables:
    MCP_AUTH_JWT_ALG: JWT algorithm (e.g., RS256, HS256)
    MCP_AUTH_JWT_SECRET: Shared secret for HMAC algorithms (HS256/384/512)
    MCP_AUTH_JWT_PUBLIC_KEY: Public key for RSA/EC algorithms
    MCP_AUTH_JWT_JWKS_URI: JWKS endpoint URL (alternative to public_key)
    MCP_AUTH_JWT_ISSUER: Expected token issuer
    MCP_AUTH_JWT_AUDIENCE: Expected token audience
    MCP_AUTH_REQUIRED_SCOPES: Comma-separated default required scopes
    MCP_AUTH_AUTHORIZATION_SERVERS: Comma-separated authorization server URLs
    MCP_AUTH_BASE_URL: This server's base URL for OAuth metadata

Usage in components:
    from fastmcp.server.auth import require_scopes
    from fastmcp.tools import tool

    @tool(auth=require_scopes("admin"))
    def admin_only_tool() -> str:
        return "secret data"
"""

import os

from src.core.logging import get_logger

log = get_logger("auth")


def configure_auth():
    """Create an auth provider from environment variables, or None if not configured."""
    alg = os.getenv("MCP_AUTH_JWT_ALG")
    if not alg:
        log.debug("No MCP_AUTH_JWT_ALG set; auth disabled")
        return None

    secret = os.getenv("MCP_AUTH_JWT_SECRET")
    public_key = os.getenv("MCP_AUTH_JWT_PUBLIC_KEY")
    jwks_uri = os.getenv("MCP_AUTH_JWT_JWKS_URI")

    if not (secret or public_key or jwks_uri):
        log.warning("MCP_AUTH_JWT_ALG set but no key/secret/JWKS URI provided; auth disabled")
        return None

    # Lazy import to avoid pulling in auth deps when auth is disabled
    from fastmcp.server.auth import JWTVerifier, RemoteAuthProvider

    issuer = os.getenv("MCP_AUTH_JWT_ISSUER")
    audience = os.getenv("MCP_AUTH_JWT_AUDIENCE")
    required_scopes_raw = os.getenv("MCP_AUTH_REQUIRED_SCOPES", "")
    required_scopes = [s.strip() for s in required_scopes_raw.split(",") if s.strip()] or None

    # For HMAC algorithms, the "secret" is passed as public_key
    key = public_key or secret

    verifier = JWTVerifier(
        public_key=key,
        jwks_uri=jwks_uri,
        algorithm=alg,
        issuer=issuer,
        audience=audience,
        required_scopes=required_scopes,
    )

    # If authorization server URLs are provided, wrap in RemoteAuthProvider
    # for full OAuth 2.0 Protected Resource metadata (RFC 9728)
    auth_servers_raw = os.getenv("MCP_AUTH_AUTHORIZATION_SERVERS")
    base_url = os.getenv("MCP_AUTH_BASE_URL")

    if auth_servers_raw and base_url:
        auth_servers = [s.strip() for s in auth_servers_raw.split(",") if s.strip()]
        auth = RemoteAuthProvider(
            token_verifier=verifier,
            authorization_servers=auth_servers,
            base_url=base_url,
        )
        log.info(f"Auth enabled: JWTVerifier ({alg}) with RemoteAuthProvider")
        return auth

    # Without OAuth metadata, return the verifier directly
    # Note: This works for simple JWT validation but won't advertise OAuth metadata
    log.info(f"Auth enabled: JWTVerifier ({alg})")
    return verifier
