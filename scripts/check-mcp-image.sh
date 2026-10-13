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
# one non-JSON line in front of the first response (DIST-001). Only stdout is
# parsed here, while stderr is kept and shown when the check fails -- suppressing
# it entirely made a container that died at startup fail with no output at all.
#
# Usage: scripts/check-mcp-image.sh <image-ref>
set -euo pipefail

IMAGE="${1:?usage: check-mcp-image.sh <image-ref>}"

out="$(mktemp)"
err="$(mktemp)"
trap 'rm -f "$out" "$err"' EXIT

# The requests, then stdin is held open until the answers land -- a bounded wait,
# not fixed sleeps. The first version slept a fixed 6 s and raced: a cold runner
# can take longer than that to start the container and import Python, the server
# then read EOF on the way in, and the check reported "no tools" -- a server
# defect that was the harness's (PR-Agent on #195). The writer sees the answer in
# the same file the reader is filling, so the wait ends as soon as it can.
if ! {
    printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"check-mcp-image","version":"1"}}}'
    printf '%s\n' '{"jsonrpc":"2.0","method":"notifications/initialized"}'
    printf '%s\n' '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
    for _ in $(seq 1 45); do
        grep -q '"id":2' "$out" 2>/dev/null && break
        sleep 1
    done
} | docker run -i --rm "$IMAGE" >"$out" 2>"$err"; then
    echo "the container did not exit cleanly. Its stderr was:" >&2
    cat "$err" >&2
    exit 1
fi

if ! python3 - "$out" <<'PY'
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
then
    echo "--- the container's stderr ---" >&2
    cat "$err" >&2
    exit 1
fi
