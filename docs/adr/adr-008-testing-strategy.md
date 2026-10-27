# ADR-008: Testing Strategy — TDD + Mutation Testing

- **Status:** ACCEPTED
- **Date:** 2026-06-19
- **Deciders:** Manu
- **Relates to:** pattern-testing-standards, pattern-integration-testing

## Context

The project needs comprehensive testing at multiple levels: unit tests for core logic, integration tests for API endpoints, AI mocking strategy, and mutation testing to validate test quality.

## Decision

### Testing Pyramid

```
                    ┌─────────┐
                    │  E2E    │  ← Manual / occasional
                    │  (5%)   │
                   ┌┴─────────┴┐
                   │ Integration│  ← FastAPI TestClient + mocked AI
                   │   (25%)    │
                  ┌┴────────────┴┐
                  │   Unit Tests  │  ← Core, AI client, session, storage
                  │    (70%)      │
                  └───────────────┘
```

### Unit Tests

Per `pattern-testing-standards`:

```python
# Naming: test_<unit>_<scenario>_<expected>
def test_pdf_modifier_single_replacement_preserves_font():
    ...

def test_session_manager_expired_session_returns_none():
    ...

def test_throttle_respects_concurrency_limit():
    ...
```

**Fixtures:**
- `tmp_path` for all file I/O (never write to real project dir)
- `monkeypatch.delenv()` to strip real API keys
- Null/mock clients for AI service (never real API calls in unit tests)
- `@pytest.fixture` with `session` scope for expensive resources

### Integration Tests

Per `pattern-integration-testing`:

```python
# CLI → API pipeline test
def test_upload_then_structure_then_replace(tmp_path, client):
    # 1. Upload PDF
    pdf = tmp_path / "test.pdf"
    pdf.write_bytes(SAMPLE_PDF)
    resp = client.post("/api/pdf/upload", files={"file": pdf.open("rb")})
    session_id = resp.json()["session_id"]

    # 2. Get structure
    resp = client.get(f"/api/pdf/{session_id}/structure")
    assert resp.status_code == 200
    assert resp.json()["total_pages"] > 0

    # 3. Replace
    resp = client.post(f"/api/pdf/{session_id}/replace", json={
        "replacements": {"old": "new"}
    })
    assert resp.json()["replacements_made"] > 0

    # 4. Download
    resp = client.get(f"/api/pdf/{session_id}/download")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
```

### AI Mocking Strategy

Per `pattern-integration-testing` Section 3:

| Test Level | Mock Strategy | Why |
|---|---|---|
| Unit tests | `unittest.mock.patch` on client class | Fast, deterministic |
| Integration tests | NullLLMClient injection | Tests wiring, not external API |
| Smoke tests | Real NaN Cloud call | Validates actual path (behind `--live` flag) |

```python
# Null client for tests
class NullAIClient:
    async def chat_completions(self, **kwargs):
        return {"choices": [{"message": {"content": "{}"}}]}

# Fixture
@pytest.fixture
def mock_ai():
    return NullAIClient()
```

### Mutation Testing

Per `pattern-testing-standards`:

```toml
# pyproject.toml
[tool.mutmut]
paths_to_mutate = ["src/pdf_modifier/"]
tests_dir = "tests/"
runner = "python -m pytest"
use_coverage = true
coverage_file = ".coverage"
```

**Targets:**
- Minimum mutation score: 70%
- Target mutation score: 80%+
- Run in CI on every PR
- Block merge if score drops

**Manual mutations for core:**

| Mutant | Original | Mutated | Must kill? |
|---|---|---|---|
| Off-by-one | `for page in doc` | `for page in doc[:-1]` | Yes |
| Font map wrong | `("helv", "Helvetica")` | `("Cour", "Courier")` | Yes |
| Regex mode | `.search(text)` | `.match(text)` | Yes |
| Color bit shift | `>> 16` | `>> 8` | Yes |
| Guard removal | `if not items: continue` | (delete line) | Yes |

### Coverage Targets

| Layer | Minimum | Target |
|---|---|---|
| Core (PDFModifier, PDFAnalyzer) | 85% | 95% |
| AI Layer (client, router, throttle) | 80% | 90% |
| Web Routes | 75% | 85% |
| Session + Storage | 80% | 90% |
| **Global** | **80%** | **85%+** |

### Test File Organization

```
tests/
├── conftest.py                  # Shared fixtures
├── test_core/                   # Existing tests (no changes)
│   ├── test_modifier.py
│   ├── test_analyzer.py
│   └── test_models.py
├── test_ai/                     # NEW
│   ├── test_client.py           # Mock httpx
│   ├── test_router.py           # Unit test real
│   ├── test_throttle.py         # Unit test real
│   └── test_prompts.py          # Template rendering
├── test_web/                    # NEW
│   ├── test_pdf_routes.py       # FastAPI TestClient
│   ├── test_ai_routes.py        # Mock AI service
│   ├── test_session.py          # Unit test real
│   └── test_storage.py          # tmp_path
└── test_integration/            # NEW
    ├── test_upload_flow.py      # Full E2E
    └── test_ai_flow.py          # AI detection flow
```

### CI Integration

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: uv run pytest --cov=src --cov-report=xml --cov-fail-under=80

- name: Run mutation tests
  run: uv run mutmut run

- name: Check mutation score
  run: |
    SCORE=$(uv run mutmut results | grep "killed" | awk '{print $3}')
    if [ "$SCORE" -lt 70 ]; then
      echo "Mutation score $SCORE% is below minimum 70%"
      exit 1
    fi
```

## Amendment (2026-10-27): the minimum is enforced as a ratchet

The CI step sketched above was never wired in: the real workflow ended its score
step in `|| true`, so no minimum was enforced. When enforcement started (#223) the
suite measured 64.6%, below the 70% minimum. Turning the gate on at 70% would have
made the mutation job red on every backend PR, so the gate starts as a ratchet:

- `.github/workflows/mutation.yml` fails below `MUTATION_SCORE_FLOOR`, which starts
  at 64, the measured baseline rounded down.
- Score = (killed + timeout) / (killed + timeout + survived + suspicious). Mutants
  with no tests are excluded.
- The floor is raised as surviving mutants are killed and is never lowered to let a
  PR pass. The 70% minimum and the 80% target above still stand as the destination.

## Consequences

- Tests catch regressions early
- Mutation testing validates test quality (not just coverage)
- AI mocking prevents flaky tests and API key leaks
- Integration tests catch schema drift between layers
- TDD enforced via `pattern-testing-standards`

## Alternatives Considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| Coverage-only (no mutation) | Simpler CI | High coverage with weak assertions | **Rejected** |
| Real AI calls in CI | More realistic | Flaky, burns quota, leaks keys | **Rejected** |
| No integration tests | Faster | Misses wiring bugs between layers | **Rejected** |
| Playwright E2E tests | Full browser testing | Overkill for MVP, slow CI | **Deferred** |
