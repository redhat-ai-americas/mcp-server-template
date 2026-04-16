---
description: Update project docs to reflect actual implementation — README, ARCHITECTURE, and any file that still carries stale template-language references
---

# Update Documentation

You are updating the project documentation so it reflects the actual implemented components AND no longer reads as if the project is the upstream template it was scaffolded from.

This is the step where the project graduates from "a copy of the template" to "a standalone project that happens to have been built from the template." That means two things, both of which this command must handle:

1. **Component docs** — README/ARCHITECTURE sections that enumerate tools, resources, prompts, and middleware must match what's actually in `src/`.
2. **Template-language drift** — docs inherited from the template baseline frequently still say things like "MCP Server Template", "this template provides...", or "Contributing to MCP Server Template". In a real project, those read as self-references and confuse anyone reading the repo. Scrub them.

Do both.  Reporting only that you updated README and ARCHITECTURE and leaving `CONTRIBUTING.md` titled "Contributing to MCP Server Template" is a failure mode — that's what was happening before this skill was expanded.

## Prerequisites Check (MANDATORY)

**Before proceeding, verify that example code has been removed.**

Check if these directories/files exist:
- `src/tools/examples/`
- `src/resources/examples/`
- `src/prompts/examples/`
- `src/middleware/examples/`
- `tests/examples/`

If ANY of these exist, STOP and tell the user:

```
Cannot update documentation while example code is present.

Please run ./remove_examples.sh first to remove the example implementations.
This ensures the documentation reflects your actual tools, not the template examples.

After removing examples, run /update-docs again.
```

**DO NOT proceed if examples still exist.**

## Your Task (After Examples Removed)

The task has three phases: component documentation, template-language sweep, and test-file sanity check. Run all three — do NOT stop after phase 1.

---

## Phase 1: Component Documentation

### Step 1.1: Inventory Components

#### Tools (src/tools/)
For each `.py` file (excluding `__init__.py` and `_` prefixed files):
- Tool name
- Description (from docstring)
- Parameters (name, type, description)
- Return type

#### Resources (src/resources/)
For each `.py` file in `src/resources/` and subdirectories:
- Resource URI pattern
- Description
- Return type (MIME type if available)

#### Prompts (src/prompts/)
For each `.py` file (excluding `__init__.py` and `_` prefixed files):
- Prompt name
- Description
- Parameters

#### Middleware (src/middleware/)
For each `.py` file:
- Middleware name
- Purpose
- What lifecycle hooks it implements

### Step 1.2: Update README.md

Update the README.md to include:

#### Tools Section
```markdown
## Tools

| Tool | Description |
|------|-------------|
| `tool_name` | Brief description |
| `another_tool` | Brief description |

### tool_name

[Detailed description]

**Parameters:**
- `param1` (type, required): Description
- `param2` (type, optional): Description

**Example:**
```json
{
  "param1": "value"
}
```
```

#### Resources Section (if any resources exist)
```markdown
## Resources

| URI Pattern | Description |
|-------------|-------------|
| `data://resource/{id}` | Brief description |
```

#### Prompts Section (if any prompts exist)
```markdown
## Prompts

| Prompt | Description |
|--------|-------------|
| `prompt_name` | Brief description |
```

Also: if the README title still reads "FastMCP Server Template" or similar, change it to name this specific project.

### Step 1.3: Update ARCHITECTURE.md

If ARCHITECTURE.md exists, update the components section to reflect:
- Actual tool count and names
- Resource patterns
- Prompt definitions
- Middleware in use
- Any dependencies between components

If ARCHITECTURE.md doesn't exist, create a minimal version:

```markdown
# Architecture

## Component Overview

This MCP server provides [N] tools, [N] resources, [N] prompts, and [N] middleware components.

### Tools

[List actual tools with brief descriptions]

### Resources

[List actual resources with URI patterns]

### Prompts

[List actual prompts]

### Middleware

[List middleware and their purposes]

## Data Flow

[Describe how data flows through the server]

## Dependencies

[List external dependencies and why they're needed]
```

---

## Phase 2: Template-Language Drift Sweep

The template baseline ships several docs whose content actively refers to "the MCP Server Template." In a real project, those self-references are misleading. Scrub them surgically.

### Step 2.1: Scan for drift

Run these searches across the project (exclude `.venv/`, `.git/`, `__pycache__/`):

```bash
# Explicit template-name references
grep -rn -E 'mcp-server-template|MCP Server Template|FastMCP Server Template' . \
    --include='*.md' --include='*.py' --include='*.toml' --include='*.yaml' \
    --include='*.yml' --include='Makefile' --include='CODEOWNERS' \
    --exclude-dir=.venv --exclude-dir=.git --exclude-dir=__pycache__

# Indirect self-references ("this template", "the template provides", etc.)
grep -rn -iE '\bthis template\b|\bthe template provides\b|\btemplate repositor' . \
    --include='*.md' --include='*.py' --include='*.toml' --include='*.yaml' \
    --include='*.yml' --include='Makefile' \
    --exclude-dir=.venv --exclude-dir=.git --exclude-dir=__pycache__
```

### Step 2.2: Classify each hit

Not every match is drift — classify each:

| Category | Example | Action |
|---|---|---|
| **Drift (self-reference)** | `# Contributing to MCP Server Template` at top of CONTRIBUTING.md | **Fix** — rewrite to name this project |
| **Drift (indirect)** | "This template provides slash commands..." in CLAUDE.md | **Fix** — "This project provides slash commands..." |
| **Legitimate upstream pointer** | `[rdwj/mcp-server-template](https://github.com/rdwj/mcp-server-template)` | **Keep** |
| **Provenance metadata** | `.template-info` JSON referencing the template URL | **Keep** |
| **Jinja2 sense** | "Renders the template with your provided variables" in `.fips-agents-cli/README.md` | **Keep** (different meaning of "template") |
| **Accurate description** | "(from the template base)" describing a dependency's origin | **Keep** |

### Step 2.3: Files that commonly need fixes

Based on the template baseline, expect drift in these files. Check each:

- **`CONTRIBUTING.md`** — title is usually "Contributing to MCP Server Template"; clone URL uses `mcp-server-template.git`. Rewrite the title and the clone URL to this project. Keep a brief pointer to the upstream template for readers who want the scaffold.
- **`AGENTS.md`** — often has "this template provides a structured workflow" and "Template Structure" section heading. Rewrite the framing as "this project was built using a structured workflow..." with a pointer to the upstream; rename the section to "Project Structure."
- **`DEVELOPMENT_PROCESS.md`** — opens with "workflow for developing MCP servers using this template." Reframe as "the workflow used to build this server."
- **`CLAUDE.md`** — typically says "This template provides slash commands for a structured development workflow." Rewrite to "This project provides slash commands (in `.claude/commands/`)..."
- **`TESTING.md`** and **`OPENSHIFT_DEPLOYMENT.md`** — check for template-specific framing; usually generic enough to keep but confirm.
- **`Makefile`** — `help` target's `@echo` banner often reads "MCP Server Template - Available Commands." Rewrite to name this project.
- **`.github/CODEOWNERS`** — leading comment often says "CODEOWNERS file for mcp-server-template." Rewrite.

Apply surgical edits — do not wholesale rewrite files. Fix only the drift; leave unrelated content alone.

---

## Phase 3: Test-File Sanity Check

The template ships end-to-end tests that hardcode example tool/resource/prompt names (`echo`, `analyze_text`, `get_weather`, `readme_snippet`, `japan_profile`, etc.). After `remove_examples.sh`, these tests break at import time or assertion time.

### Step 3.1: Scan for broken references

```bash
grep -rn -E '\b(echo|get_weather|analyze_text|configure_system|format_text|calculate_statistics|process_data|validate_input|write_release_notes|delete_all|readme_snippet|japan_profile|passport_lost_protocol|first_international_trip_checklist)\b' tests/ \
    --include='*.py' 2>/dev/null
```

### Step 3.2: If matches are found

Offer two options:
1. **Rewrite** the test against the current tools (preferred if the test exercises a generic property like "server discovers N tools"). Parameterize against the actual tool names.
2. **Delete** the test if it was specific to example behavior and has no analogue in the current project.

For a file like `tests/test_server_e2e.py` that's entirely built around example discovery, the cleanest fix is usually a minimal rewrite: parameterize the discovery test over the current tool names, keep the HTTP transport smoke test, drop the rest.

After fixing, run `.venv/bin/pytest tests/ -v --ignore=tests/examples/` and confirm the suite is green before declaring success.

---

## Phase 4: Verify

After Phases 1–3, re-run the drift scan from Phase 2.1 and confirm every remaining match falls into a **Keep** category. If any **Fix** category hits remain, loop back.

Also sanity-check:
1. Every tool listed in docs has a corresponding file in `src/tools/`
2. Parameter types and descriptions match the implementation
3. No example tool names are mentioned in docs (echo, analyze_text, etc.)
4. Tool/resource/prompt counts in prose match the actual counts
5. `pytest tests/ --ignore=tests/examples/` is still green

## Phase 5: Report

Provide a summary:

```markdown
## Documentation Update Summary

### Component documentation (Phase 1)
- README.md: [N] tools, [N] resources, [N] prompts documented
- ARCHITECTURE.md: [what was updated or created]

### Template-language drift (Phase 2)
- Files scrubbed: [list]
- Remaining "template" references (all legitimate): [brief classification]

### Test fixes (Phase 3)
- Files updated: [list, or "none needed"]
- Suite status: [N passed / N failed]

### Components
- **Tools**: [list tool names]
- **Resources**: [list resource patterns]
- **Prompts**: [list prompt names]
- **Middleware**: [list middleware names]
```

## Important Guidelines

- **NEVER proceed if examples directory exists** — this is a hard requirement.
- **All three phases run together** — Phase 1 alone is incomplete. A project with perfect README tool docs but a CONTRIBUTING.md titled "Contributing to MCP Server Template" is not done.
- **Prefer surgical edits** — fix only the drifted lines; leave unrelated content alone. Don't rewrite CLAUDE.md or AGENTS.md wholesale just because two lines need to change.
- **Keep upstream pointers** — legitimate references to the template (URLs, provenance metadata, "built from rdwj/mcp-server-template") are valuable attribution. Only scrub references that read as self-descriptions.
- **Match parameter names exactly** — typos in docs cause confusion.
- **Include usage examples** — concrete examples are more useful than descriptions.
- **Update counts** — if docs say "3 tools" make sure there are actually 3 tools.

## What NOT to Document

- `__init__.py` files
- Internal helper functions (prefixed with `_`)
- Test files (but DO fix them if they break due to example removal — Phase 3)
- Development utilities

## Error Cases

### Examples Still Present
```
STOP: Example directories found. Run ./remove_examples.sh first.
```

### No Tools Found
```
WARNING: No tools found in src/tools/.
Either tools haven't been implemented yet, or there's a directory structure issue.
Consider running /create-tools first.
```

### Documentation Can't Be Parsed
If README.md or ARCHITECTURE.md have unexpected structure:
```
The existing [file] has an unexpected structure.
I can either:
1. Overwrite with a fresh template (loses existing content)
2. Append the component documentation at the end
3. Show you the proposed changes for manual integration

Which approach would you prefer?
```

### Tests Break After Example Removal
If `pytest tests/` shows failures that all reference removed example names, that's the expected Phase 3 case — fix or delete the offending test files (usually `tests/test_server_e2e.py`). Don't declare the skill done while tests are red.
