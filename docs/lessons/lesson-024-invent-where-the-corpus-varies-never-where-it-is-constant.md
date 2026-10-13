---
id: lesson-024-invent-where-the-corpus-varies-never-where-it-is-constant
type: lesson
status: active
created: "2026-10-13"
owner: manu
tags: [lesson, testing, fixtures, synthetic-data, verification]
---

# Invent where the corpus varies; never where it is constant

**Context:** A synthetic receipt was being written to reproduce a defect that only a real document had shown. Four real examples of that receipt were on screen, used as the source of truth for the shape: same layout, same block, same labels, the same card.
**Problem:** The card number was **invented** — `Acct ****3777` became `****8192` — while all four examples carried `3777`. The card is the field that does **not** vary: it is the same account every time. The fields that *do* vary (amounts, dates, the reference being replaced) were the ones available to change, and they were left as they were. The result was a "realistic" fixture that could not exist, and the change looked deliberate rather than mistaken, because a card number is exactly the field a hand would alter to make sample data anonymous. Read by **column** instead of by row, the four examples said which fields were constant in one glance; read as four stories, they said nothing about it.
**Solution:** Separate a corpus into constant and varying fields before writing anything synthetic, and treat the two halves differently. **Constants are copied** — their whole value is that they are what the real thing looks like, and inventing them silently breaks the fixture's resemblance to the case it exists for. **Variables are invented**, and that is the only place invention buys anonymity. A corpus read by column is what makes the split visible; a corpus read by row is a set of stories with no column in common. The corollary for review: a value that looks invented in a fixture is a signal, not a style — ask which column it came from, and if the answer is "the one that never changes", the fixture no longer reproduces the case it was built for.
**Tags:** `#testing` `#fixtures` `#synthetic-data` `#verification`
