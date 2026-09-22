# anysearch-mcp-guide

Notes and runnable examples for wiring AnySearch into an MCP client.

Why this exists: I kept re-deriving the same three things every time I set up
AnySearch in a new tool. The MCP spec moves faster than the blog posts, half the
snippets online still use the old `sse_client`, and the error messages when auth
fails are not helpful. So this is the version I wish I'd had: copy the config,
run the example, get on with it.

AnySearch itself is a search + retrieval API. You give it a query, it returns
ranked results with extracted page text. It is exposed over MCP as a server that
registers a handful of tools (`search`, `extract`, `get_sub_domains`) and one
resource template. You talk to it like any other MCP server.

Tested against:
- Python 3.11.7 on Ubuntu 22.04 and macOS 14.4
- `mcp` Python SDK 1.2.x
- Node 20.11 (`@modelcontextprotocol/sdk` 1.0.x)
- Claude Desktop 0.7.x, Cursor 0.42

Not tested on Windows. The stdio examples *should* work there but I don't own a
Windows box and I'm not going to claim otherwise.

## What's in here

```
docs/advanced-config.md     env vars, timeouts, HTTP transport, multiple servers
docs/tools-reference.md     every tool, its schema, and what it returns
examples/python/sdk_usage.py   minimal MCP client that calls search
examples/python/streaming.py   streaming server example (FastMCP)
examples/node/usage.mjs        same thing with the TS/JS SDK
examples/curl/advanced_curl.md hitting the HTTP transport by hand
CHANGELOG.md
```

## Install

Python side:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install "mcp>=1.2,<2"
```

Node side:

```bash
npm install @modelcontextprotocol/sdk
```

Get an AnySearch key from the dashboard and export it. Do not hardcode it.

```bash
export ANYSEARCH_API_KEY=YOUR_ANYSEARCH_KEY
```

## MCP client config (stdio)

This is the part people actually want. Drop it in your client's config file
(`claude_desktop_config.json`, `.cursor/mcp.json`, whatever your client uses):

```json
{
  "mcpServers": {
    "anysearch": {
      "command": "anysearch-mcp",
      "args": ["--transport", "stdio"],
      "env": {
        "ANYSEARCH_API_KEY": "YOUR_ANYSEARCH_KEY"
      }
    }
  }
}
```

If `anysearch-mcp` isn't on your PATH, use an absolute path. This is the single
most common cause of "server failed to start" in the client log. The client
launches the command itself, so `~` is not expanded and your shell's PATH is not
sourced.

## Quick usage

Call the tool from Python. Full script is in `examples/python/sdk_usage.py`.

```python
import asyncio, os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main() -> None:
    params = StdioServerParameters(
        command="anysearch-mcp",
        args=["--transport", "stdio"],
        env={"ANYSEARCH_API_KEY": os.environ["ANYSEARCH_API_KEY"]},
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print([t.name for t in tools.tools])
            res = await session.call_tool(
                "search", {"query": "mcp streamable http spec", "max_results": 3}
            )
            print(res.content[0].text)

asyncio.run(main())
```

Expected output (trimmed):

```
['search', 'extract', 'get_sub_domains']
1. Model Context Protocol — Transports (modelcontextprotocol.io)
   Streamable HTTP replaces the HTTP+SSE transport...
```

## Gotchas / troubleshooting

**`Connection refused` / client says server exited immediately.**
Usually the command isn't found, or it crashed on import. Run the exact command
by hand first: `anysearch-mcp --transport stdio`. If it prints a Python
traceback, you have your answer. stdio servers must not write anything to
stdout that isn't a JSON-RPC frame. `print()` in your server code will corrupt
the stream and the client will report a parse error, not your bug.

**401 with `{"error":"unauthorized"}`.**
The key is missing or wrong. Note that MCP clients do *not* inherit your shell
env unless you put it in the `env` block. Setting `ANYSEARCH_API_KEY` in
`.bashrc` and then wondering why Claude Desktop 401s is a rite of passage.

**`tool not found: serch`.**
Tool names are exact and case-sensitive. Call `list_tools` and print the names
instead of guessing. Typos in tool names come back as a protocol-level error, so
the message is terse.

**Empty results but HTTP 200.**
Your query matched nothing. `search` returns `{"results": []}`, not an error.
Check `total_results` if you're paginating.

**Timeouts on `extract` for large pages.**
The default request timeout is 30s. Big pages with lots of JS sometimes need
more. See `docs/advanced-config.md` for `ANYSEARCH_TIMEOUT`.

## Notes

The `sse_client` transport is deprecated. If you're copying an example from a
2024 blog post and it imports `from mcp.client.sse import sse_client`, it will
still run against servers that haven't migrated, but new servers should use
Streamable HTTP. Both are documented in `docs/advanced-config.md`.

I wrote `examples/python/streaming.py` because I wanted to see how partial
results look over the wire. It is not how the hosted AnySearch server works, it
is a toy you can run locally to understand the framing.

Issues and corrections welcome. If a command in here is wrong for your version,
open an issue with the version number.
