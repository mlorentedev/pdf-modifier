# Specs — PDF Modifier MCP Evolution

> Planning session output: 2026-06-19
> All specs ready for implementation by qwen3.6

## Overview

This directory contains the complete specification for evolving PDF Modifier MCP from a CLI + MCP server into a full web platform with AI capabilities.

## Specs

> Status as of 2026-10-06. Archived specs live in [`archive/`](archive/).

| ID | Feature | Phase | Status | Effort |
|---|---|---|---|---|
| [WEB-001](WEB-001-web-ui/) | Web UI for PDF editing | 1 | SHIPPED, archive pending (#169) | ~12 days |
| [AI-001](AI-001-detection/) | AI-powered document detection | 2 | SHIPPED, archive pending (#169) | ~6.5 days |
| [VIS-001](VIS-001-vision/) | Vision and OCR capabilities | 3 | NOT STARTED (#73) | ~4.5 days |
| [ML-001](ML-001-multilingual/) | Multilingual and semantic | 4 | NOT STARTED (#74) | ~5.5 days |
| [AUD-001](AUD-001-audio/) | Audio (TTS/STT) | 5 | NOT STARTED (#75) | ~5 days |
| [INFRA-001](INFRA-001-docker/) | Docker infrastructure | Parallel | SHIPPED, archive pending (#169) | ~5 days |
| [FONT-001](FONT-001-custom-fonts/) | Custom fonts & font resolver | — | SHIPPED, archive pending (#169) | — |

**Total estimated effort: ~38.5 days (~8 weeks)**

## ADRs

| ADR | Decision | Status |
|---|---|---|
| [ADR-001](../docs/adr/adr-001-web-architecture.md) | Web Architecture: FastAPI + SvelteKit | ACCEPTED |
| [ADR-002](../docs/adr/adr-002-ai-layer.md) | AI Layer: Centralized with Model Router + Throttle | ACCEPTED |
| [ADR-003](../docs/adr/adr-003-pdf-storage.md) | PDF Storage: Filesystem with Session TTL | ACCEPTED |
| [ADR-004](../docs/adr/adr-004-session-management.md) | Session Management: In-memory with TTL | ACCEPTED |
| [ADR-005](../docs/adr/adr-005-async-strategy.md) | Async Strategy: anyio.to_thread for sync core | ACCEPTED |
| [ADR-006](../docs/adr/adr-006-deployment.md) | Deployment: Docker on VPS (Kubelab) | ACCEPTED |
| [ADR-007](../docs/adr/adr-007-security.md) | Security: Defense in Depth | ACCEPTED |
| [ADR-008](../docs/adr/adr-008-testing-strategy.md) | Testing: TDD + Mutation Testing | ACCEPTED |
| [ADR-009](../docs/adr/adr-009-frontend.md) | Frontend: SvelteKit with PDF.js | ACCEPTED |
| [ADR-010](../docs/adr/adr-010-vision-pipeline.md) | Vision Pipeline: PDF→Image→mimo-v2.5 | ACCEPTED |
| [ADR-011](../docs/adr/adr-011-semantic-search.md) | Semantic Search: Embedding + Rerank Pipeline | ACCEPTED |
| [ADR-012](../docs/adr/adr-012-audio-pipeline.md) | Audio Pipeline: TTS/STT with Chunking | ACCEPTED |

## Implementation Order

```
Week 1-2:  INFRA-001 (Docker) + WEB-001 Phase 1-2 (Backend)
Week 3:    WEB-001 Phase 3 (Frontend)
Week 4:    WEB-001 Phase 4 (Integration) + AI-001 Phase 1 (Client)
Week 5:    AI-001 Phase 2-3 (Endpoints + Frontend)
Week 6:    VIS-001 (Vision + OCR)
Week 7:    ML-001 (Multilingual + Semantic)
Week 8:    AUD-001 (Audio) + Final integration
```

## Dependencies

```
INFRA-001 ─────────────────────────────────┐
                                            │
WEB-001 ───────┬───────────────────────────┤
               │                           │
AI-001 ────────┼───────┬───────────────────┤
               │       │                   │
VIS-001 ───────┼───────┼───────────────────┤
               │       │                   │
ML-001 ────────┼───────┼───────────────────┤
               │       │                   │
AUD-001 ───────┴───────┴───────────────────┘
```

## NaN Cloud Models Used

| Model | Used In | Purpose |
|---|---|---|
| mimo-v2.6-flash | AI-001, VIS-001 | Vision, tool calling, reasoning |
| qwen3.6 | AI-001, ML-001 | Translation, summary, fast tasks |
| gemma4 | AI-001 | Fallback model |
| qwen3-embedding | ML-001 | Semantic search embeddings |
| rerank | ML-001 | Search result reranking |
| kokoro | AUD-001 | Text-to-speech |
| whisper | AUD-001 | Speech-to-text |

## Vault Patterns Applied

| Pattern | Applied In |
|---|---|
| pattern-architecture | ADR-001 (monolith structure) |
| pattern-async-threading | ADR-005 (anyio.to_thread) |
| pattern-container-workflow | INFRA-001 (multi-stage Docker) |
| pattern-decision-persistence | ADRs (all decisions documented) |
| pattern-integration-testing | ADR-008 (E2E test strategy) |
| pattern-mcp-tool-design | Existing MCP server (preserved) |
| pattern-nan-builders-gateway | ADR-002 (throttle, fallback) |
| pattern-python-cli | Existing CLI (preserved) |
| pattern-secrets-security | ADR-007 (gitleaks, age) |
| pattern-spec-driven-development | All specs (proposal + tasks + verification) |
| pattern-testing-standards | ADR-008 (TDD, mutation) |
| pattern-workflow-protocol | Knowledge placement (ADRs in repo) |
