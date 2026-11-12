---
id: "lesson-007-canvas-render-must-run-after-dom-mount-in-sve"
type: lesson
status: active
title: "Canvas render must run after DOM mount in Svelte {#if}"
created: "2026-08-04"
owner: manu
tags: [pdf-modifier-mcp, lesson, frontend, svelte, canvas, lifecycle]
---

# Canvas render must run after DOM mount in Svelte {#if}

**Context:** Rendering a PDF to a `<canvas>` inside a Svelte `{#if loading}` block.
**Problem:** `renderPage()` called in `onMount` silently no-oped — the canvas was wrapped in `{#if loading}`, so it wasn't in the DOM yet and `canvas` was `null`. Result: black screen, no error.
**Solution:** Set `loading = false` first, `await tick()` to let Svelte flush the DOM, then call `renderPage()`. Also: reactive prop changes (e.g. `highlightText`) need a `$effect` to trigger re-render — calling once in `onMount` isn't enough.
**Tags:** `#frontend` `#svelte` `#canvas` `#lifecycle`
