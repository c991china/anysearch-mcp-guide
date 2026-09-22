"""A toy MCP server that reports progress while it works, plus a client.

This is NOT the hosted AnySearch server. I wrote it to see how partial progress
looks on the wire, because "streaming" in MCP means progress notifications and
log messages, not a token stream. Two different things and people conflate them.

Run it directly to watch the notifications:
    pip install "mcp>=1.2,<2"
    python examples/python/streaming.py

What to notice: the server calls ctx.report_progress() as it goes. The client
passes a progress_callback and prints each update. Nothing here blocks on a
network call, so it finishes in under a second.
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.fastmcp import Context, FastMCP

mcp = FastMCP("progress-demo")


@mcp.tool()
async def slow_sum(count: int, ctx: Context) -> int:
    """Sum 0..count, reporting progress as we go.

    Deliberately does real work in chunks so the progress notifications have
    something to describe.
    """
    if count < 0:
        # Raise, don't return a sentinel. MCP turns this into isError=true.
        raise ValueError("count must be >= 0")

    total = 0
    for i in range(1, count + 1):
        total += i
        if i % max(1, count // 5) == 0:
            await ctx.report_progress(progress=i, total=count)
    return total


async def _client() -> int:
    params = StdioServerParameters(
        command=sys.executable,
        args=[__file__, "--serve"],
        env=None,
    )

    def on_progress(progress: float, total: float | None, _message: Any) -> None:
        total_s = int(total) if total else "?"
        pct = (progress / total * 100) if total else 0
        print(f"  progress {int(progress)}/{total_s} ({pct:.0f}%)")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write, progress_callback=on_progress) as session:
            await session.initialize()
            result = await session.call_tool("slow_sum", {"count": 1000})
            if result.isError:
                print(f"failed: {result.content[0].text}", file=sys.stderr)
                return 1
            print(f"result: {result.content[0].text}")
    return 0


def main() -> None:
    # The same file is both server and client, selected by argv. Cheaper than
    # shipping two files for a demo.
    if "--serve" in sys.argv:
        mcp.run(transport="stdio")
        return
    raise SystemExit(asyncio.run(_client()))


if __name__ == "__main__":
    main()
