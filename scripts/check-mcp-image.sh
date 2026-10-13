#!/usr/bin/env bash
# Smoke-test the MCP distribution image: does it speak MCP on stdio, and does
# stdout carry NOTHING but JSON-RPC?
#
# Run by .github/workflows/docker-build.yml on every pull request that touches
# the root Dockerfile. Glama's own build test is this handshake, so failing here
# is failing before a third party's builder reports it.
#
# Why the second assertion exists: a stdio MCP server that works in a terminal
# and fails on the wire is almost always a stray `print()` on stdout, and it
# looks fine in a shell where stdout and stderr are the same stream. Measured
# case: PyMuPDF 1.28.2 prints a deprecation warning on `import fitz`, which put
# one non-JSON line in front of the first response (DIST-001). `2>/dev/null` here
# is deliberate: it is the only way to see what a client actually sees.
#
# Usage: scripts/check-mcp-image.sh <image-ref>
set -euo pipefail

IMAGE="${1:?usage: check-mcp-image.sh <image-ref>}"

out="$(mktemp)"
trap 'rm -f "$out"' EXIT

# The pauses are not padding: closing stdin immediately after the last request
# tears the container down before it answers it, which reads as "the server did
# not reply to tools/list" when the server was fine.
{
    printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"check-mcp-image","version":"1"}}}'
    sleep 2
    printf '%s\n' '{"jsonrpc":"2.0","method":"notifications/initialized"}'
    sleep 1
    printf '%s\n' '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
    sleep 3
} | docker run -i --rm "$IMAGE" >"$out" 2>/dev/null

python3 - "$out" <<'PY'
import json
import sys

lines = [line for line in open(sys.argv[1]).read().splitlines() if line.strip()]

stray = [line for line in lines if not line.startswith("{")]
if stray:
    sys.exit(
        f"stdout carried {len(stray)} non-JSON line(s); a stdio MCP server's stdout is "
        f"the JSON-RPC channel: {stray[:3]}"
    )
if not lines:
    sys.exit("the image answered nothing on stdout")

messages = [json.loads(line) for line in lines]
answers = {message.get("id"): message for message in messages}
errors = [m for m in messages if "error" in m]
if errors:
    sys.exit(f"the server answered with an error: {errors[0]['error']}")

init = answers.get(1, {}).get("result", {})
server = init.get("serverInfo", {}).get("name")
if not server:
    sys.exit(f"no initialize result with a serverInfo.name: {init or 'absent'}")
if not init.get("protocolVersion"):
    sys.exit(f"initialize answered without a protocolVersion: {init}")

tools = answers.get(2, {}).get("result", {}).get("tools")
if not tools:
    sys.exit("tools/list answered with no tools")

print(f"ok: {server} answered initialize ({init['protocolVersion']}) and lists {len(tools)} tools")
print("    " + ", ".join(tool["name"] for tool in tools))
PY
