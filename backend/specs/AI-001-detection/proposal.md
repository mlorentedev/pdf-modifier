---
id: "AI-001"
type: spec
status: active
created: "2026-06-19"
feature: AI-Powered Document Detection
---

# AI-001: AI-Powered Document Detection

## What

Add AI capabilities to detect document fields, classify document types, and redact PII automatically using NaN Cloud models (mimo-v2.6-flash for vision/tool calling, qwen3.6 for fast tasks).

## Why

- Manual field detection is tedious and error-prone
- PII redaction needs to be automatic for compliance
- Document classification enables smart form generation
- Differentiates PDF Modifier from basic text editors

## Scope

### In Scope
- AI client for NaN Cloud (httpx, OpenAI-compatible)
- Model router with fallback chain
- Throttle/rate limiting
- Auto-detect fields endpoint
- Document classification endpoint
- PII redaction endpoint
- AI panel in frontend

### Out of Scope
- Vision/OCR (see VIS-001)
- Translation (see ML-001)
- Audio (see AUD-001)

## Acceptance Criteria

1. [ ] AI client connects to NaN Cloud API
2. [ ] `enable_thinking: false` sent in every request
3. [ ] Rate limiting respects NaN Cloud limits
4. [ ] Auto-detect returns structured field list
5. [ ] Classification returns document type
6. [ ] PII redaction identifies NIF, email, phone, credit card
7. [ ] AI panel in frontend shows results
8. [ ] All AI tests use mocked responses (no real API in unit tests)
9. [ ] Fallback works on 429/5xx errors

## Technical Notes

- ADR-002: AI Layer architecture
- ADR-005: Async strategy (httpx async)
- `pattern-nan-builders-gateway`: Rate limits, `enable_thinking: false`
- `pattern-testing-standards`: Mock at boundary, null client for tests
