---
id: "lesson-001-decoupled-file-based-logging-for-mcp-servers"
type: lesson
status: active
title: "Decoupled File-based Logging for MCP Servers"
created: "2026-03-07"
owner: manu
tags: [pdf-modifier-mcp, lesson, mcp, observability, logging, cli]
---

# Decoupled File-based Logging for MCP Servers

**Context:** Adding background observability to a CLI/MCP tool without polluting the standard output.
**Problem:** When deploying an MCP server, stdout/stderr is often consumed by the MCP transport protocol (stdio). If a silent error happens in production, there's no way to debug it because the LLM context only shows generic fallback error messages.
**Solution:** Created a centralized `logger.py` that implements a `RotatingFileHandler` writing directly to `~/.pdf-modifier/logs/pdf-modifier.log`. This decoupled file-based logging captures stack traces and unhandled exceptions natively, providing a "black box" flight recorder for debugging without breaking the MCP stdio JSON protocol.
**Tags:** `#mcp` `#observability` `#logging` `#cli`
