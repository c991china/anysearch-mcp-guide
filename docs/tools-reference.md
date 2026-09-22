# Tools reference

What the AnySearch MCP server registers. Schemas are the real `inputSchema`
values from `list_tools`, abridged only where noted. Every tool returns
`content` as an array; the first element is `type: "text"` with a JSON string
body unless noted otherwise.

If a call fails, the server returns `isError: true` and a text block with a
human-readable message. Protocol-level failures (bad params) come back as
JSON-RPC errors instead, which is why the two look different.

---

## `search`

Ranked web results for a query. This is the one you'll use 90% of the time.

Input schema:

```json
{
  "type": "object",
  "properties": {
    "query":       { "type": "string", "minLength": 1 },
    "max_results": { "type": "integer", "minimum": 1, "maximum": 50, "default": 10 },
    "region":      { "type": "string", "enum": ["us", "eu", "ap"] },
    "recency":     { "type": "string", "enum": ["day", "week", "month", "year"] },
    "domains":     { "type": "array", "items": { "type": "string" } }
  },
  "required": ["query"]
}
```

Result body:

```json
{
  "query": "mcp streamable http",
  "total_results": 128,
  "results": [
    {
      "title": "Transports - Model Context Protocol",
      "url": "https://modelcontextprotocol.io/specification/...",
      "snippet": "Streamable HTTP replaces the HTTP+SSE transport...",
      "score": 0.94,
      "published": "2025-03-26"
    }
  ]
}
```

Notes:
- `max_results` is capped at 50. Asking for 200 gets you a validation error, not
  a clamp. I'd prefer a clamp; the server disagrees.
- `domains` is an include-list, not a filter-out. There's no exclude syntax yet.
- `published` is often missing. Don't build UI that assumes it's there.
- `total_results` is an estimate. It drifts between identical calls.

---

## `extract`

Fetch one URL and return cleaned main-content text. Use this when `search` gives
you a URL you want the body of.

Input schema:

```json
{
  "type": "object",
  "properties": {
    "url":            { "type": "string", "format": "uri" },
    "max_chars":      { "type": "integer", "default": 20000, "maximum": 200000 },
    "include_links":  { "type": "boolean", "default": false }
  },
  "required": ["url"]
}
```

Result body:

```json
{
  "url": "https://example.com/post",
  "title": "How we shard Postgres",
  "text": "Main article text, boilerplate stripped...",
  "truncated": false,
  "links": []
}
```

Notes:
- `truncated: true` means `max_chars` cut it off. Raise the limit or accept it.
- The extractor is readability-style heuristics. Pages that render content
  entirely client-side return a near-empty `text`. Nothing to fix on your end.
- 404s from the target come back as `isError: true` with the status code, not as
  a JSON-RPC error. Same for TLS failures, which show up as a cert message.

---

## `get_sub_domains`

Subdomain enumeration for a host. Handy for recon and for finding the docs site
when someone put it on `docs.internal.example.com` and never linked it.

Input schema:

```json
{
  "type": "object",
  "properties": {
    "domain": { "type": "string" },
    "limit":  { "type": "integer", "default": 100, "maximum": 1000 }
  },
  "required": ["domain"]
}
```

Result body:

```json
{ "domain": "example.com", "count": 3, "subdomains": ["www.example.com", "docs.example.com", "api.example.com"] }
```

Notes:
- This is passive (certificate transparency + DNS datasets), not a live brute
  force. It will not find an internal-only host.
- Results are deduped and lowercased. Order is not stable.

---

## Resources

The server exposes one resource template:

```
anysearch://cache/{url_hash}
```

It serves the last extracted body for a URL, keyed by the SHA-256 of the
normalized URL. Useful if you extract the same page repeatedly and don't want to
re-fetch. The cache is in-memory and dies with the process, so this is only a
win within one session. No TTL; entries are evicted LRU at 200 items.

Read it like any resource:

```python
res = await session.read_resource("anysearch://cache/9f2c...e1")
print(res.contents[0].text)
```

If you don't know the hash, there is no `list_resources` for it. I know. It's a
gap. Compute the hash yourself or just call `extract` again.

---

## Prompts

None registered as of 0.4.0. If you're building a client that expects a prompt
catalog, handle the empty case.

## Error shapes you'll actually see

| Situation | Shape |
| --- | --- |
| Missing `query` | JSON-RPC error `-32602`, "missing required property query" |
| `max_results: 200` | JSON-RPC error `-32602`, "value must be <= 50" |
| Bad API key | `isError: true`, text `{"error":"unauthorized"}` |
| Rate limited (429) | `isError: true`, text `{"error":"rate_limited","retry_after":5}` |
| Target site down | `isError: true`, text with the upstream status |
| Unknown tool name | JSON-RPC error `-32601`, "method not found" |

The split between `isError` and JSON-RPC errors is intentional: the first is
"the tool ran and the world said no", the second is "you called it wrong". Most
clients render them differently, so it's worth knowing which is which when
you're debugging.
