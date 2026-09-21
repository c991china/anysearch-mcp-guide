# AnySearch MCP 安装与设置指南（公开版）

> 面向 AI Agent 的搜索基础设施，通过 MCP / API / Skill 接入。
> 本仓库为**公开、脱敏**版本：**不含任何私密 API Key**。请自行在控制台获取你自己的 Key。

---

## 1. AnySearch 是什么

AnySearch 是一个**面向 AI Agent（智能体）的搜索后端**，不是给人用的普通搜索引擎。它让 AI 应用/智能体能够联网检索高质量、结构化的信息。

核心特性：

- **意图理解 + 自动路由**：问一句，自动判断去哪个数据源查，无需手动选源。
- **结构化输出**：返回 Agent 能直接消费的结构化结果，减少 token 浪费。
- **三种接入方式**：原生 **API**、**MCP**（Model Context Protocol）、**Skill**。
- **安全隐私**：匿名使用、无追踪、零遥测。
- 官方对标 Brave Search API，基准测试显示准确率 76.4%、端到端延迟比 Brave/Parallel 快约 30%+。

---

## 2. 获取 API Key

API Key 是调用 AnySearch 的**鉴权凭证**。带 Key 的访问比匿名访问有更高的速率上限。Key 是**可选的**（匿名也能用，但限速更低）。

### 方式一：自动注册（一行搞定，无需验证码）

用你的**真实可用邮箱**作为账号用户名，接口会直接返回一个一次性明文 Key：

```bash
curl -s -X POST "https://api.anysearch.com/v1/auth/email/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com"}'
```

返回示例（`code: 0` 表示成功）：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "username": "you@example.com",
    "email": "you@example.com",
    "login_url": "https://www.anysearch.com/login",
    "api_key": {
      "id": "key_xxxxxxxx",
      "key": "as_sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
      "key_prefix": "as_sk_xxxxxx...",
      "name": "default",
      "rate_limit": 100,
      "quota_limit": 0,
      "expires_at": null,
      "created_at": "2026-06-23T10:23:00Z"
    }
  }
}
```

> ⚠️ `api_key.key` **只显示一次**，请立即保存。也可之后在控制台重新查看。

### 方式二：控制台手动创建（推荐，最稳妥）

直接访问 https://www.anysearch.com/console/api-keys 创建免费 Key。

---

## 3. 配置 MCP（远程 HTTP，无需本地安装）

AnySearch 提供的是**远程 Streamable HTTP** MCP 服务，无需本地安装任何包。

写入用户级配置（如 WorkBuddy 的 `~/.workbuddy-ai/mcp.json`）：

```json
{
  "mcpServers": {
    "anysearch": {
      "type": "http",
      "url": "https://api.anysearch.com/mcp",
      "headers": {
        "Authorization": "Bearer as_sk_你的KEY",
        "X-Anysearch-Client": "mcp/1.0.0"
      }
    }
  }
}
```

把 `as_sk_你的KEY` 替换成你在控制台拿到的真实 Key。

要点：

- `type`: `http`（远程 Streamable HTTP 直连，无需 SSE/stdio 代理）。
- `url`: 生产端点 `https://api.anysearch.com/mcp`。
- `Authorization`: `Bearer <你的 Key>`。
- `X-Anysearch-Client`: 固定客户端标识 `mcp/1.0.0`。

### 信任启用（关键，不能跳过）

远程 MCP server 写入配置后**不会自动生效**，必须在客户端（如 WorkBuddy 连接器管理页）找到 **anysearch** 并点击 **Trust（信任）** 启用。

---

## 4. 连通性验证

配置并信任后，可用下面的命令验证 endpoint 是否可达、Key 是否鉴权通过：

```bash
curl -s -i -X POST "https://api.anysearch.com/mcp" \
  -H "Authorization: Bearer as_sk_你的KEY" \
  -H "X-Anysearch-Client: mcp/1.0.0" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
```

成功标志：返回 `HTTP 200`，且 `result.serverInfo.name` 为 `anysearch-mcp-server`。

---

## 5. 可用工具与调用建议

AnySearch MCP 暴露 4 个工具：

| 工具 | 作用 |
|------|------|
| `search` | 普通/垂直领域搜索（金融、学术、安全、代码等） |
| `get_sub_domains` | 查询垂直领域目录，返回可用的 `sub_domain` 及参数 schema |
| `batch_search` | 一次并行执行 1–5 个独立搜索，单条失败不影响其余 |
| `extract` | 抓取某个 URL 全文并转为 Markdown（上限 50,000 字符） |

### 官方推荐的两条路由路径

**Path A — 通用搜索（默认）**：新闻、概念、人物、公司、URL 核实、最新动态、对比等**非结构化**查询 → 直接 `search` 或 `batch_search`，不带 domain。

**Path B — 垂直搜索（结构化字段）**：股票代码、DOI、CVE、航班码、经纬度、专利号等 → 先 `get_sub_domains` 查到正确的 `sub_domain` 和参数，再 `search`。

**不确定时 → 用 `batch_search` 混合**：同一次调用里同时发一条通用 + 一条垂直查询，覆盖面比猜更强。

---

## 6. 安全提示

- **不要把 API Key 提交到公开仓库或公开文档**。本仓库已做脱敏处理。
- 客户端配置文件中若写入 Key，注意文件访问权限。
- Key 优先级：`Authorization` 头 > 环境变量 `ANYSEARCH_API_KEY` > `.env` > 匿名访问（限速最低）。
- 额度耗尽时，AnySearch 可能返回新 Key，确认后持久化即可。

官方安装指南：https://anysearch.com/install/mcp-install.md
