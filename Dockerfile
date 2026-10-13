# =============================================================================
# Distribution image for the MCP directories — pdf-modifier (stdio MCP server)
#
# Glama builds a crawled server "from source" with a Dockerfile from the
# repository ROOT, and this one is deliberately SINGLE-STAGE: its builder does
# not consume the multi-stage `backend/Dockerfile` and falls back to an
# auto-generated image that times out, which is why the listing's build fails
# (DIST-001). The MCP server is a pure-Python package, so there is no compiler
# stage to strip and nothing to gain from one.
#
# `backend/Dockerfile` is the FastAPI image and is untouched: that one serves the
# API behind nginx, with a health check on a port. This one serves one process
# over stdin/stdout, which is what MCP's stdio transport is.
#
# Dependency resolution is unpinned (`pip install .` reads pyproject's ranges), so
# a break can arrive with no commit of ours: PyMuPDF has already announced that
# the `fitz` shim this package imports will be removed (CORE-002). CI mitigates
# that only partly -- `.github/workflows/docker-build.yml` builds this image and
# runs the MCP handshake on every change that touches it, which catches a break on
# the next such PR, not one that lands between them, and Glama rebuilds an old
# commit on its own schedule. The three ways to close it are a periodic rebuild
# (CI-003), bounding the dependency, or pinning the resolve.
# =============================================================================
FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.title="pdf-modifier" \
      org.opencontainers.image.description="Text modification in PDFs, preserving layout and fonts, as an MCP server." \
      org.opencontainers.image.source="https://github.com/mlorentedev/pdf-modifier" \
      org.opencontainers.image.licenses="MIT"

# The user is created BEFORE the source is copied, so editing the source does not
# invalidate this layer (and a non-root runtime is what the image is for).
RUN groupadd --gid 1000 mcp && \
    useradd --uid 1000 --gid mcp --create-home --shell /bin/bash mcp

WORKDIR /app

# Only what the wheel build needs. A whole-context COPY would ship the frontend,
# the lockfiles and any local `.env` into a published image.
COPY backend/pyproject.toml backend/README.md backend/LICENSE ./
COPY backend/src ./src

RUN pip install --no-cache-dir . && rm -rf /root/.cache/pip

# PyMuPDF writes its own messages with `print()` to STDOUT, which in a stdio
# MCP server is the JSON-RPC channel. Measured: PyMuPDF 1.28.2 prints
# "warning: The `fitz` API is deprecated..." on `import fitz`, so the image's
# stdout carried one non-JSON line before the first response. `fd:2` is PyMuPDF's
# own switch for where those messages go — no wrapper, no core change, and the
# diagnostics stay visible on stderr. `scripts/check-mcp-image.sh` fails if this
# ever regresses.
ENV PYMUPDF_MESSAGE=fd:2

USER mcp

# The console script declared in pyproject.toml, which runs the FastMCP server on
# the stdio transport — the same command `smithery.yaml` publishes and the same
# one Glama's check starts before it asks for the tool list.
CMD ["pdf-modifier"]
