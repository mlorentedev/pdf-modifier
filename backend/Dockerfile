# =============================================================================
# Backend Dockerfile — pdf-modifier (FastAPI)
# Multi-stage: builder (download wheels) → runtime (install + run, non-root)
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Builder — download wheels to avoid network in runtime
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS builder

WORKDIR /build

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv && \
    uv pip compile pyproject.toml --python-version 3.12 -q -o requirements.txt && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2: Runtime — minimal image, non-root user
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

# Venv lives OUTSIDE /app so volume mounts don't overwrite it
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install wheels (no network needed)
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy source and install package
COPY pyproject.toml ./
COPY src/ ./
COPY server.json CHANGELOG.md LICENSE README.md ./
RUN pip install --no-cache-dir .

# Verify critical binaries exist
RUN python -c "import uvicorn; print(f'uvicorn {uvicorn.__version__}')" && \
    which uvicorn

# Runtime directories
RUN mkdir -p /app/.pdf-modifier/logs /app/storage && chown -R appuser:appuser /app /opt/venv

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

USER appuser

CMD ["uvicorn", "pdf_modifier.web.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
