# Retrospective: FastMCP 3.x Migration

**Date:** 2026-04-06
**Effort:** Migrate MCP server template from FastMCP 2.x to 3.x
**Commits:** `617c57f` (main migration), `6f645c0` (generator templates)

## What We Set Out To Do

- Replace custom `loaders.py` with FastMCP's `FileSystemProvider`
- Switch all components from shared `@mcp.tool` to standalone `@tool` decorators
- Replace hand-rolled JWT auth (`BearerVerifier`) with built-in `JWTVerifier`/`RemoteAuthProvider`
- Remove shipped FastMCP docs in favor of online references (gofastmcp.com)
- Update all tests, docs (CLAUDE.md, README.md, ARCHITECTURE.md), and slash commands
- Pin to FastMCP >=3.2.0

## What Changed

| Change | Type | Rationale |
|--------|------|-----------|
| Removed `watchdog` dependency | Good pivot | `FileSystemProvider(reload=True)` replaces it natively |
| Removed `pyjwt` dependency | Good pivot | FastMCP 3.x bundles JWT verification |
| `LoggingMiddleware` import path correction | Bug caught in testing | Not re-exported from `fastmcp.server.middleware`; actual path is `.logging.LoggingMiddleware` |
| Test agent over-engineered with mocking scaffolding | Fixed in review | Added compatibility shims for hypothetical missing v3.x APIs; unnecessary since we control the venv |
| Removed dead `_preview_prompt_utility.py` reference from `remove_examples.sh` | Cleanup | File hasn't existed; guard was harmless but misleading |

## What Went Well

- Parallel sub-agent strategy worked cleanly: core infra and component updates ran simultaneously with zero file conflicts
- Review agent caught real issues (stale `__init__.py` refs, wrong middleware import path, README/ARCHITECTURE staleness) that would have shipped otherwise
- Net deletion of ~13.7k lines by removing shipped docs -- template is much leaner
- 32/32 tests pass against actual FastMCP 3.2.1-dev
- Grep verification confirmed zero stale v2.x patterns in source code
- `FileSystemProvider` is a major simplification: deleted 200+ lines of custom loader code, hot-reload plumbing, and watchdog integration

## Gaps Identified

| Gap | Severity | Resolution |
|-----|----------|------------|
| No end-to-end server startup test | Follow-up | [#4](https://github.com/redhat-ai-americas/mcp-server-template/issues/4) |
| Auth pipeline untested with real JWT tokens | Follow-up | [#5](https://github.com/redhat-ai-americas/mcp-server-template/issues/5) |
| `fips-agents generate` may still emit v2.x scaffolds | Fixed | [#6](https://github.com/redhat-ai-americas/mcp-server-template/issues/6) — fixed in `6f645c0` + CLI `0dc642f` |
| No container build verification | Accept | Containerfile unchanged; low risk |

## Action Items

- [x] Fix `remove_examples.sh` dead code
- [x] File follow-up issues (#4, #5, #6)
- [x] Commit, PR to main, merge (PR #7)

## Patterns

**Start:** Verify import paths against actual package `__init__.py` exports before using them. The `LoggingMiddleware` import issue would have been caught earlier with a quick `python -c "from X import Y"` check.

**Continue:** Parallel sub-agent execution for independent code areas. Review agent as a separate pass after implementation agents finish. Running real tests against the actual dependency (not mocked) to catch integration issues.
