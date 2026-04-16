---
description: Deploy MCP server to OpenShift with pre-flight checks AND live verification
---

# Deploy MCP Server

You are deploying an MCP server to OpenShift.  Deployment is complete only when the server has been proven to respond correctly over its public route — not when the pod is running.  A terminal-worker's "pod ready" report is necessary but not sufficient.

**The most common failure mode with this skill is stopping after the terminal-worker reports success.**  The pod can be healthy while the tool schemas are wrong, the route is misconfigured, TLS is mangling the body, or the server is registering zero tools because of an import error that doesn't prevent startup.  Only a live mcp-test-mcp round-trip proves the deployment works.  Phase 4 is not optional.

## Arguments

- **PROJECT**: (required) The OpenShift project/namespace name (e.g., `weather-mcp`).  Each MCP server should deploy to its own project to avoid naming collisions.

## Phases

The skill has four phases, all mandatory:

1. **Prereqs** — environment, auth, availability of verification tooling
2. **Pre-deployment checks** — permissions, tests, secrets, docker ignore
3. **Build & deploy** — delegated to a terminal-worker subagent
4. **Live verification** — mcp-test-mcp round-trip against the real route

Do not skip ahead to the summary based on Phase 3's success message.

---

## Phase 1: Prereqs

### 1.1  Verify the verification tool is available *before* deploying

Look for these tools in your available MCP tools:

- `mcp__mcp-test-mcp__connect_to_server`
- `mcp__mcp-test-mcp__list_tools`
- `mcp__mcp-test-mcp__call_tool`
- `mcp__mcp-test-mcp__disconnect`

If any are missing, STOP before building anything and tell the user:

```
STOP: mcp-test-mcp is not available.  Please enable it and run /deploy-mcp again.
A deploy isn't complete without a live verification step, and without mcp-test-mcp
I can't prove the deployed route works.
```

Do NOT proceed to a build if verification tooling is missing.  Catching this now saves you from deploying a server you then can't verify.

### 1.2  Verify the OpenShift context

```bash
oc whoami
oc whoami --show-server
oc config current-context
```

If `oc whoami` returns an auth error, STOP and ask the user to log in with `! oc login ...` (the `!` prefix runs it in the chat so the result is visible).  Do NOT attempt the deploy against an unauthenticated cluster — it will fail late and noisily.

### 1.3  Prior workflow steps should have run

The deploy assumes:

- `/create-tools` has implemented the tools and written tests.
- `/exercise-tools` has vetted ergonomics and error messages.
- `/update-docs` has been run (and therefore `./remove_examples.sh` has run, the test suite has been scrubbed of references to removed example tools, and docs reflect the actual server).

If the repo still contains `src/*/examples/` directories or `tests/test_server_e2e.py` references to removed example tool names like `echo` / `get_weather`, loop back to `/update-docs` before deploying.

---

## Phase 2: Pre-deployment Checks

### 2.1  Permission fix

Claude Code's Write tool creates files with `600` permissions; OpenShift containers run as arbitrary non-root UIDs that need at least `644`.

```bash
find src -name "*.py" -perm 600 -exec chmod 644 {} \; -print | wc -l
find src -name "*.py" -perm 600 | wc -l   # should be 0
```

### 2.2  `.dockerignore` covers the big offenders

Confirm `.dockerignore` excludes:
- `__pycache__/`
- `.venv/`
- `tests/`
- `.env`

### 2.3  Tests are green

```bash
.venv/bin/pytest tests/ -v
```

If tests fail, STOP and report.  Do not deploy broken code, even if the failures look unrelated.

### 2.4  No obvious secrets in source

```bash
grep -rn "password\s*=" src/ --include="*.py" || true
grep -rn "api_key\s*=" src/ --include="*.py" || true
grep -rn "secret\s*=\s*['\"]" src/ --include="*.py" || true
grep -rn "token\s*=\s*['\"]" src/ --include="*.py" || true
```

If any real (non-fixture, non-placeholder) match appears, stop and ask the user before proceeding.  Remember that test fixtures with self-labelling names like `"test-secret-do-not-use-in-production"` are fine.

---

## Phase 3: Build & Deploy

Use the Task tool to launch a `terminal-worker` subagent with this prompt (substitute the project name):

```
Build and deploy the MCP server to OpenShift project `<PROJECT>`.

Your job is to run the build+deploy commands and report pod health.
You are NOT responsible for verifying the deployed server responds
correctly -- the main agent does that separately in a later phase.

Run these commands in sequence.  Use `-n <PROJECT>` on every oc command;
do not run `oc project`:

1. `make deploy PROJECT=<PROJECT>`     # kicks off the BuildConfig
2. `oc rollout status deployment/mcp-server -n <PROJECT> --timeout=300s`
3. `oc get pods -n <PROJECT>`
4. `oc logs -l app=mcp-server -n <PROJECT> --tail=40`
5. `oc get route -n <PROJECT> -o jsonpath='{.items[0].spec.host}'`

If the deployment uses a different deployment name or label, adjust
accordingly.  Report:

- Whether `make deploy` succeeded (last 20 lines of build log if failed)
- Pod status (Running/Ready or the actual condition)
- First signs of server startup from the log tail (look for "Starting
  FastMCP" or similar — report any stack traces verbatim)
- The route hostname, so the main agent can build the MCP URL
- Any errors or warnings encountered

Do NOT declare the deploy "successful" or "complete".  Report what you
observed and return control.
```

When the terminal-worker returns, the pod should be running and you should have the route hostname.  **That is not success.**  Proceed to Phase 4.

---

## Phase 4: Live Verification (MANDATORY)

**Do not skip this phase.  Do not summarize before completing it.**

Build the full MCP URL: `https://<route-host>/mcp/` (the trailing slash matters).

### 4.1  Connect

```
mcp__mcp-test-mcp__connect_to_server(url="https://<route-host>/mcp/")
```

If connection fails, investigate: check the route host, verify `/mcp/` path (trailing slash is required), re-read pod logs for startup errors.  Do not paper over a connection failure — the deploy is broken.

### 4.2  Tool inventory

```
mcp__mcp-test-mcp__list_tools()
```

Assert:
- Every tool the code defines in `src/tools/` appears in the response
- No tools you *don't* expect leak through (template examples, debug tools)
- The tool schemas (descriptions, parameter constraints, enums) match what `src/tools/*.py` declares — this is the single best check that the container has the latest code

If a tool is missing from the live server, the most common causes are:
- Container still has an older image: check `oc describe pod ...` for the image tag
- Import error on one of the tool modules: check `oc logs` for tracebacks
- `__init__.py` or file permissions: rerun the Phase 2.1 permission fix

### 4.3  Happy-path round-trip

Pick a tool and make a realistic call:

```
mcp__mcp-test-mcp__call_tool(
  name="<tool_name>",
  arguments={...realistic inputs...}
)
```

Assert the result has the expected shape and at least one field value matches expectations.  The goal is to prove the full request/response path — not just that the tool is listed.

### 4.4  Error-path round-trip

Call a tool with input you know should raise a `ToolError` (bad syntax, missing required parameter, out-of-range value).  Assert:

- The error surfaces as a structured `ToolError`, not a generic 500
- The coaching message the tool writes is preserved end-to-end through the HTTP transport

This proves that structured error propagation works — a thing you cannot verify from pod logs.

### 4.5  Disconnect

```
mcp__mcp-test-mcp__disconnect()
```

If any of 4.1–4.4 failed, the deploy has a problem.  Report it clearly, do not declare success.

---

## Phase 5: Report

After (and only after) Phase 4 has completed successfully, produce a summary:

```markdown
## Deployment Summary

**Project**: <PROJECT>
**Route**: https://<route-host>/mcp/
**Status**: SUCCESS

### Pre-deployment Checks
- [x] Permissions fixed (N files)
- [x] .dockerignore verified
- [x] Tests passed (N/N)
- [x] No hardcoded secrets

### Build & Deploy
- [x] BuildConfig completed
- [x] Pod `<name>` Running and Ready (1/1)
- [x] Server started (log excerpt: ...)

### Live Verification
- [x] Connected to https://<route-host>/mcp/ (~Nms)
- [x] Tool inventory: N/N expected tools registered, schemas match
- [x] Happy path: <tool_name> returned <expected>
- [x] Error path: <tool_name> with bad input → ToolError with coaching message intact

### Next Steps
- Point an MCP client at https://<route-host>/mcp/ (see SYSTEM_PROMPT.md if generated)
- Monitor with `oc logs -f -l app=mcp-server -n <PROJECT>`
```

If anything is incomplete — including if Phase 4 was skipped or partially done — the status is **NOT** SUCCESS.  Use INCOMPLETE or FAILED and explain what's outstanding.

---

## Important Guidelines

- **Phase 4 is not optional.**  A terminal-worker's pod-is-running report is necessary but not sufficient for deployment success.  Stopping at Phase 3 is the most common failure mode this skill sees — resist the pull to summarize.
- **Namespace via `-n`, not `oc project`.**  Multiple simultaneous Claude Code sessions on the same cluster would collide otherwise.
- **Use terminal-worker for the build.**  The build output is verbose; keeping it out of main context keeps your reasoning space clean.
- **Verify availability of mcp-test-mcp BEFORE building.**  Do not discover mid-deploy that you can't verify.
- **Each MCP server gets its own OpenShift project.**  Don't share namespaces between unrelated servers.
- **Never `oc delete` shared resources** without asking the user.  The cluster may host other projects you don't know about.

---

## Error Recovery

### Build fails

- `requirements.txt` vs `pyproject.toml` drift — dependencies must be in BOTH
- Import errors on container startup — `python -c "from src.main import main"` locally first
- File permissions — rerun Phase 2.1

### Pod won't start / CrashLoopBackoff

- `oc logs deployment/<name> -n <PROJECT> --previous` for the failed container's logs
- Missing env vars — check `openshift.yaml` against what `src/core/server.py` expects
- `PermissionError` in the traceback — almost always the `600`-permissions issue; rerun Phase 2.1 and redeploy

### mcp-test-mcp can't connect

- Is the URL exactly `https://<host>/mcp/` with the trailing slash?
- Is the Route `Admitted`?  `oc describe route -n <PROJECT>`
- Is TLS terminating at the edge? Check `oc get route -o yaml` for the `tls:` block
- Pod logs for startup errors (sometimes server binds locally but fails on first HTTP request)

### Tool missing from live `list_tools` response

- The most likely cause is an older image.  `oc describe pod -n <PROJECT>` shows the image digest; compare with the latest BuildConfig build.  Trigger a new build if the pod is on an older image.
- Second most likely: an import error in the tool's module that doesn't crash the server but prevents `FileSystemProvider` from registering the tool.  Check `oc logs` for tracebacks at startup.

### Error-path verification fails (tool error returns wrong shape)

- Check that the tool raises `fastmcp.exceptions.ToolError`, not a bare `Exception`.
- Confirm the coaching string isn't being truncated by an error-handling middleware you added.
- Streamable-HTTP should serialize `ToolError.message` into a structured error — if it's showing up as a 500, something is catching and re-raising incorrectly.
