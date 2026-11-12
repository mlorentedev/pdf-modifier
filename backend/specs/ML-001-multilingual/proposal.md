---
id: "ML-001"
type: spec
status: active
created: "2026-06-19"
feature: Multilingual and Semantic Capabilities
---

# ML-001: Multilingual and Semantic Capabilities

## What

Add translation, semantic search, summarization, and structured data extraction using NaN Cloud models (qwen3.6 for text tasks, qwen3-embedding for embeddings, rerank for reranking).

## Why

- PDFs are often in foreign languages
- Semantic search finds concepts, not just exact text
- Summarization saves reading time
- Structured extraction converts PDFs to JSON for integration

## Scope

### In Scope
- Translation endpoint (qwen3.6)
- Semantic search endpoint (qwen3-embedding + rerank)
- Summarization endpoint (qwen3.6)
- Structured extraction endpoint (mimo-v2.6-flash tool calling)
- Frontend integration

### Out of Scope
- Real-time translation (batch only)
- Multi-document search (single PDF only)

## Acceptance Criteria

1. [ ] Translation maintains layout and fonts
2. [ ] Semantic search returns relevant results
3. [ ] Summarization produces coherent summaries
4. [ ] Extraction returns valid JSON
5. [ ] All endpoints use correct models

## Technical Notes

- qwen3.6: 35B/3B, 256K context, fast, good for text tasks
- qwen3-embedding: 8B, 4096 dim, 100+ languages
- rerank: 8B, 1000 RPM, improves search precision
