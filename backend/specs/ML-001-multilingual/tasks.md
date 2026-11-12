---
id: "ML-001-tasks"
type: spec-tasks
status: active
created: "2026-06-19"
---

# ML-001: Tasks — Multilingual and Semantic

## TDD Workflow

For each task: RED (write failing test) → GREEN (implement) → REFACTOR (clean up).

---

## Phase 1: Embedding Infrastructure

### T1.1: Embedding Client
- [ ] **RED:** Write `test_embedding_returns_vector`
- [ ] **RED:** Write `test_embedding_batch_respects_limit`
- [ ] **GREEN:** Create `src/pdf_modifier/ai/embedding.py`
- [ ] **GREEN:** Implement `get_embedding(text) → list[float]`
- [ ] **GREEN:** Implement `get_embeddings_batch(texts) → list[list[float]]`
- [ ] **GREEN:** Use qwen3-embedding model
- [ ] **REFACTOR:** Add batch size limit (32)

### T1.2: Rerank Client
- [ ] **RED:** Write `test_rerank_returns_sorted_results`
- [ ] **GREEN:** Implement `rerank(query, documents) → list[RankedDoc]`
- [ ] **GREEN:** Use rerank model
- [ ] **REFACTOR:** Add relevance scores

---

## Phase 2: Multilingual Endpoints

### T2.1: Translation Endpoint
- [ ] **RED:** Write `test_translate_returns_translated_text`
- [ ] **RED:** Write `test_translate_preserves_formatting`
- [ ] **GREEN:** Implement `POST /api/ai/{session_id}/translate`
- [ ] **GREEN:** Accept target language parameter
- [ ] **GREEN:** Use qwen3.6 for translation
- [ ] **GREEN:** Return translated text per element
- [ ] **REFACTOR:** Support batch translation

### T2.2: Semantic Search Endpoint
- [ ] **RED:** Write `test_search_returns_relevant_results`
- [ ] **RED:** Write `test_search_rerank_improves_precision`
- [ ] **GREEN:** Implement `POST /api/ai/{session_id}/search`
- [ ] **GREEN:** Embed PDF text elements
- [ ] **GREEN:** Embed query
- [ ] **GREEN:** Compute cosine similarity
- [ ] **GREEN:** Rerank with rerank model
- [ ] **REFACTOR:** Cache embeddings in session

### T2.3: Summarization Endpoint
- [ ] **RED:** Write `test_summarize_returns_summary`
- [ ] **RED:** Write `test_summarize_respects_max_length`
- [ ] **GREEN:** Implement `POST /api/ai/{session_id}/summarize`
- [ ] **GREEN:** Use qwen3.6 for summarization
- [ ] **GREEN:** Accept max_length parameter
- [ ] **REFACTOR:** Add streaming support

### T2.4: Structured Extraction Endpoint
- [ ] **RED:** Write `test_extract_returns_valid_json`
- [ ] **RED:** Write `test_extract_with_tool_calling`
- [ ] **GREEN:** Implement `POST /api/ai/{session_id}/extract`
- [ ] **GREEN:** Accept schema parameter
- [ ] **GREEN:** Use mimo-v2.6-flash with tool calling
- [ ] **GREEN:** Return structured JSON
- [ ] **REFACTOR:** Add schema validation

---

## Phase 3: Frontend Integration

### T3.1: Multilingual Panel
- [ ] Add "Translate" button with language selector
- [ ] Add "Search" input with semantic results
- [ ] Add "Summarize" button
- [ ] Add "Extract" button with schema input

---

## Dependencies

| Task | Depends on |
|---|---|
| T1.1-T1.2 | AI-001 (client infrastructure) |
| T2.1-T2.4 | T1.1-T1.2 |
| T3.1 | T2.1-T2.4 |

## Estimated Effort

| Phase | Tasks | Estimated LOC | Days |
|---|---|---|---|
| Phase 1: Embeddings | T1.1-T1.2 | ~150 | 1.5 |
| Phase 2: Endpoints | T2.1-T2.4 | ~400 | 3 |
| Phase 3: Frontend | T3.1 | ~120 | 1 |
| **Total** | **7 tasks** | **~670** | **~5.5** |
