"""AnySearch MCP 的 Python 调用示例（概念代码，需配合真实 SDK）。"""

import os


def search(query: str, max_results: int = 5):
    """调用 AnySearch 做一次搜索。

    实际使用时替换为官方 SDK 的调用方式；此处展示入参与返回结构。
    """
    api_key = os.environ.get("ANYSEARCH_API_KEY")
    if not api_key:
        raise RuntimeError("缺少 ANYSEARCH_API_KEY 环境变量")
    # 伪代码：真实 SDK 类似 mcp_client.call("search", query=query, top_k=max_results)
    payload = {"query": query, "top_k": max_results}
    print(f"[mock] search({payload}) with key=***{api_key[-4:]}")
    return [{"title": f"result-{i}", "score": 1 - i * 0.1} for i in range(max_results)]


if __name__ == "__main__":
    for item in search("GitHub API 用法", max_results=3):
        print(item)
