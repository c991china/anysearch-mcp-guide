# anysearch-mcp-guide

> AnySearch 的 MCP（Model Context Protocol）接入指南——让 AI Agent 直接拥有「联网搜索 / 子域名发现 / 网页抽取」能力。

## 这是什么
AnySearch 提供远程 Streamable HTTP MCP 服务，端点：

    https://api.anysearch.com/mcp

它暴露 4 个工具：
- `search`：通用网页搜索
- `get_sub_domains`：子域名发现
- `batch_search`：批量搜索
- `extract`：从 URL 抽取正文

鉴权：请求头 `Authorization: Bearer as_sk_****`（API Key 格式 `as_sk_` 开头）。匿名也可用，但限流更严。

## 快速接入
1. 拿到 API Key（本地指南 `20260921_AnySearch安装与设置指南.md` 有完整步骤）。
2. 在 WorkBuddy 的 `~/.workbuddy-ai/mcp.json` 加入：
   ```json
   {
     "mcpServers": {
       "anysearch": {
         "type": "http",
         "url": "https://api.anysearch.com/mcp",
         "headers": { "Authorization": "Bearer as_sk_你的KEY" }
       }
     }
   }
   ```
3. 在连接器页面 Trust 启用。

## 跑通第一个调用
本仓库 `examples/anysearch_client.py` 是一个零依赖的 Python 客户端，演示 `initialize -> tools/list -> tools/call(search)`：

    export ANYSEARCH_API_KEY=as_sk_xxxx
    python examples/anysearch_client.py "WorkBuddy AI 是什么"

> 想要更多可直接套用的接口代码（curl / Python），见友号 **[@22178384/api-samples](https://github.com/22178384/api-samples)** 的 `anysearch/` 目录——本指南侧重「怎么接」，示例仓库侧重「怎么调」。

## 目录
- `examples/anysearch_client.py`：最小可运行客户端
- `examples/quickstart.sh`：一键装依赖 + 运行

## 生态联动
- 调接口代码 → [@22178384/api-samples](https://github.com/22178384/api-samples)
- 通用开发片段 → [@22178384/snippet-box](https://github.com/22178384/snippet-box) / [@c991china/dev-snippets](https://github.com/c991china/dev-snippets)
