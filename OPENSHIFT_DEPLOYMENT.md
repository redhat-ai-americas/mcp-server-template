# Deploying MCP Servers to OpenShift: Key Practices

When building MCP servers destined for OpenShift, several design decisions make the difference between a smooth deployment and hours of debugging.

## Red Hat UBI Base Images

Start with `registry.redhat.io/ubi9/python-311:latest`. UBI (Universal Base Image) provides enterprise support, security updates, and compatibility with OpenShift's security model. It's also required if your environment has FIPS compliance requirements.

## Non-Root Container Execution

OpenShift runs containers as arbitrary non-root user IDs for security. This catches many developers off guard. Our Containerfile explicitly sets `USER 1001` and uses `--chown=1001:0` when copying files:

```dockerfile
COPY --chown=1001:0 src/ ./src/
USER 1001
```

A subtle gotcha: if your development tooling creates files with 600 permissions (owner-only), the arbitrary UID won't be able to read them. We fix this in the Containerfile:

```dockerfile
RUN find ./src -name "*.py" -exec chmod 644 {} \;
```

## Environment-Driven Configuration

The same codebase runs locally (STDIO for testing) and in OpenShift (streamable-http). Environment variables control the switch:

```dockerfile
ENV MCP_TRANSPORT=http \
    MCP_HTTP_HOST=0.0.0.0 \
    MCP_HTTP_PORT=8080
```

Locally, you override with `MCP_TRANSPORT=stdio` for testing with tools like `cmcp`.

## OpenShift-Native Builds

Rather than pushing containers from your laptop, use OpenShift's BuildConfig with binary builds. The deploy script:

1. Creates a filtered build context (excluding `__pycache__`, `.pyc` files)
2. Fixes any permission issues before upload
3. Triggers `oc start-build --from-dir` to build server-side

This ensures the image is built on x86_64 (avoiding Mac ARM issues) and lands directly in the internal registry.

## Health Checks and Resource Limits

Production-ready deployments need probes and resource constraints:

```yaml
livenessProbe:
  tcpSocket:
    port: 8080
  initialDelaySeconds: 10
readinessProbe:
  tcpSocket:
    port: 8080
  initialDelaySeconds: 5
resources:
  limits:
    memory: "512Mi"
    cpu: "500m"
```

## TLS Termination

OpenShift Routes handle TLS at the edge, so your container speaks plain HTTP internally:

```yaml
tls:
  termination: edge
  insecureEdgeTerminationPolicy: Redirect
```

## One-Command Deployment

Everything wraps up in a Makefile target:

```bash
make deploy PROJECT=my-mcp-server
```

This creates the project if needed, applies manifests, builds the image, and waits for rollout. The output includes the URL ready for testing with MCP Inspector.

---

**The takeaway**: Plan for non-root execution, use environment variables for transport switching, build server-side to avoid architecture mismatches, and include health checks from day one. These practices prevent the most common deployment failures.
