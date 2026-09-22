"""Minimal MCP client that talks to the AnySearch server over stdio.

Run:
    pip install "mcp>=1.2,<2"
    export ANYSEARCH_API_KEY=YOUR_ANYSEARCH_KEY
    python examples/python/sdk_usage.py "what is the streamable http transport"

The API key is read from the environment on purpose. If you hardcode it and
commit the file, that's on you.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_CMD = os.environ.get("ANYSEARCH_MCP_CMD", "anysearch-mcp")


def _server_params() -> StdioServerParameters:
    key = os.environ.get("ANYSEARCH_API_KEY")
    if not key:
        sys.exit("ANYSEARCH_API_KEY is not set. export it first.")
    return StdioServerParameters(
        command=SERVER_CMD,
        args=["--transport", "stdio"],
        # The client does NOT inherit your shell env. Pass it explicitly.
        env={"ANYSEARCH_API_KEY": key},
    )


def _first_text(result) -> str:
    """Pull the text out of a CallToolResult.

    Tools return content as a list of blocks. We only care about the first
    text block; if a tool ever returns an image this would need a check.
    """
    for block in result.content:
        if getattr(block, "type", None) == "text":
            return block.text
    return ""


async def run(query: str, max_results: int = 3) -> int:
    async with stdio_client(_server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            print(f"connected to {init.serverInfo.name} {init.serverInfo.version}")

            listed = await session.list_tools()
            names = sorted(t.name for t in listed.tools)
            print(f"tools: {names}")

            if "search" not in names:
                print("server has no 'search' tool; nothing to do", file=sys.stderr)
                return 2

            result = await session.call_tool(
                "search", {"query": query, "max_results": max_results}
            )

            if result.isError:
                # Tool-level failure: auth, rate limit, upstream. Not a crash.
                print(f"search failed: {_first_text(result)}", file=sys.stderr)
                return 1

            payload = json.loads(_first_text(result))
            hits = payload.get("results", [])
            print(f"{len(hits)} result(s) of ~{payload.get('total_results', '?')}")

            for i, hit in enumerate(hits, 1):
                title = hit.get("title") or "(no title)"
                print(f"{i}. {title}")
                print(f"   {hit.get('url', '')}")
                snippet = (hit.get("snippet") or "").strip()
                if snippet:
                    # Collapse newlines so one result stays on one visual line.
                    print(f"   {' '.join(snippet.split())[:160]}")
    return 0


def main() -> None:
    query = " ".join(sys.argv[1:]) or "model context protocol transports"
    raise SystemExit(asyncio.run(run(query)))


if __name__ == "__main__":
    main()
