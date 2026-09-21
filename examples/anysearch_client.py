#!/usr/bin/env python3
"""AnySearch MCP 最小可运行客户端（零第三方依赖）。

演示：initialize -> tools/list -> tools/call(search)
用法：
    export ANYSEARCH_API_KEY=as_sk_xxxx
    python examples/anysearch_client.py "你的查询"
"""
import json
import os
import sys
import urllib.request

ENDPOINT = "https://api.anysearch.com/mcp"


def _post(payload):
    api_key = os.environ.get("ANYSEARCH_API_KEY")
    if not api_key:
        sys.exit("缺少环境变量 ANYSEARCH_API_KEY，请先 export")
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
    # 兼容可能的 SSE 流：取最后一个 data: 行
    if "data:" in raw:
        for line in raw.splitlines():
            if line.startswith("data:"):
                raw = line[5:].strip()
    return json.loads(raw)


def main():
    query = sys.argv[1] if len(sys.argv) > 1 else "WorkBuddy AI 是什么"
    # 1) 握手
    init = _post({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "anysearch-mini-client", "version": "1.0.0"},
        },
    })
    print("== initialize ==")
    print(json.dumps(init.get("result", {}).get("serverInfo", {}), ensure_ascii=False))

    # 2) 列出工具
    tools = _post({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    names = [t["name"] for t in tools.get("result", {}).get("tools", [])]
    print("== tools ==")
    print(names)

    # 3) 调用 search
    call = _post({
        "jsonrpc": "2.0", "id": 3, "method": "tools/call",
        "params": {"name": "search", "arguments": {"query": query, "limit": 5}},
    })
    print("== search result ==")
    print(json.dumps(call.get("result", {}), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
