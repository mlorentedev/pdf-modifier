# CORE-001 — tasks, in the order they were done

## Reproduce, before touching anything

- [x] Build a synthetic fixture and confirm it reproduces the loss: a block of ten short Courier-Bold lines as **one text object per line**. The same block built with a single `insert_textbox` loses nothing — so the structure had to be the one that fails.
- [x] Cross the fixture with three replacement sizes (wider, narrower, four characters). All three lose the same two lines, which rules out "make the new text fit" as the mechanism.

## RED

- [x] Write `backend/tests/unit/core/test_replacement_preserves_following_lines.py` and watch it fail: **3 failed, 3 passed** — the multi-object cases lose `ARC: 00` and `CVM: 5E0000`; the single-object cases lose nothing.
- [x] Commit the failing test on its own (`1c0ae90`) so the RED state is in the history.

## Locate, by measurement

- [x] Redact **only** the target line's tight bounding box in isolation: three lines disappear. Consecutive line boxes overlap by **1.6 pt** (11 pt leading against 12.6 pt line height), and `apply_redactions` removes every text object that intersects.
- [x] Record and discard two hypotheses that were plausible and wrong: the replacement's rendered width, and an embedded font (`get_fonts()` reported *embedded*; the font object is base-14 with no `/FontFile`).

## GREEN

- [x] `_fit_redaction_to_its_own_text_object`: trim the rectangle away from the neighbours. The object being replaced is the one that **contains** the rect's centre; a neighbour can only overlap its edge.
- [x] Guard against an empty rectangle, which would redact nothing and leave the original text under the replacement.
- [x] `6 passed`; core suite `177 → 183`; `make check` **385 passed**, coverage **84.34%**.
- [x] Verify against the **real document** with the substitution active: `ARC` and `CVM` present, new value in place, old value gone.

## Close

- [ ] Independent adversarial review (`dotf spec review CORE-001`) — the implementer cannot sign this
- [ ] Archive to `specs/archive/CORE-001/`
