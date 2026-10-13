# ADR-001: Web Architecture — FastAPI + SvelteKit

- **Status:** ACCEPTED
- **Date:** 2026-06-19
- **Deciders:** Manu
- **Relates to:** pattern-architecture, pattern-async-threading

## Context

PDF Modifier is a CLI + MCP server for PDF text replacement. It needs a web UI to allow non-technical users to edit PDFs with drag-and-drop, visual structure editing, and AI-powered suggestions. The existing CLI and MCP interfaces must remain untouched.

The web layer is a new interface on top of the existing core (`PDFModifier`, `PDFAnalyzer`), which is reused as-is.

## Decision

Use **FastAPI** as the backend API server and **SvelteKit** as the SPA frontend.

### Why FastAPI

- Async native (important: NaN Cloud API calls are I/O-bound)
- Automatic OpenAPI docs (useful for the public API endpoint in Phase 6)
- Pydantic integration (existing models work directly)
- Well-tested with `httpx` TestClient

### Why SvelteKit

- Minimal bundle size (no virtual DOM overhead)
- Reactive UI needed for: drag-and-drop, live PDF preview overlay, form reactivity
- TypeScript-first
- Simple build pipeline
- `pdfjs-dist` for PDF rendering in the browser (no server-side rendering)

### Architecture

```
Frontend (SvelteKit :3000)
    ↕ REST API + SSE (streaming)
Backend (FastAPI :8000)
    ↕ anyio.to_thread.run_sync
Core (PDFModifier, PDFAnalyzer — sync, reused as-is)
```

## Consequences

- Two codebases (Python + TypeScript) — acceptable for clear separation of concerns
- Backend serves JSON API only; frontend serves the SPA
- Frontend build produces static files served by nginx or FastAPI's `StaticFiles`
- CORS configured for dev (`localhost:3000`) and production (Kubelab domain)

## Alternatives Considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| FastAPI + Jinja2 + HTMX | Single language, no build step | HTMX insufficient for rich PDF preview, drag-and-drop, live overlay | **Rejected** |
| Flask + React | Flask simpler | Flask is WSGI (no async), React overkill | **Rejected** |
| FastAPI + vanilla JS | No dependencies | No DX, no tooling, hard to maintain | **Rejected** |
