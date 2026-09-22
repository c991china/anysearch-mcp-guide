# Advanced configuration

Everything here is optional. The defaults work for a single AnySearch server
over stdio. Read this when you need HTTP transport, longer timeouts, or more
than one search backend in the same client.

## Environment variables

The server reads these on startup. There is no config file; env vars only. I
went back and forth on that and decided a file was one more thing to get wrong.

| Variable | Default | Notes |
| --- | --- | --- |
| `ANYSEARCH_API_KEY` | *(required)* | Sent as `Authorization: Bearer <key>`. |
| `ANYSEARCH_BASE_URL` | `https://api.anysearch.dev` | Point at a proxy or a local mock. |
| `ANYSEARCH_TIMEOUT` | `30` | Seconds. Applies per HTTP request, not per tool call. |
| `ANYSEARCH_MAX_RETRIES` | `2` | Retries on 429 and 5xx. 401/403 are never retried. |
| `ANYSEARCH_LOG_LEVEL` | `INFO` | `DEBUG` logs full request bodies. Don't ship that. |

Retries use exponential backoff starting at 0.5s. With the defaults, worst case
for a single call is roughly 30 * 3 + 0.5 + 1 = ~91 seconds. If that's too long
for your client, lower `ANYSEARCH_TIMEOUT` rather than `MAX_RETRIES`.

## stdio vs Streamable HTTP

Two transports matter.

**stdio** launches the server as a subprocess and speaks JSON-RPC over stdin and
stdout. One client, one server, no ports. This is what you want for desktop
tools. The catch: stdout is the wire. Any stray `print()` breaks the session.

**Streamable HTTP** runs the server as a normal HTTP service. The client POSTs
JSON-RPC to a single endpoint and may receive either a JSON response or an SSE
stream, depending on what the server chooses. This replaced the older
HTTP+SSE transport, which used two endpoints (one to send, one to receive) and
was a pain to put behind a load balancer.

Run the server over HTTP:

```bash
anysearch-mcp --transport http --host 127.0.0.1 --port 8765
```

Client config for HTTP:

```json
{
  "mcpServers": {
    "anysearch": {
      "url": "http://127.0.0.1:8765/mcp",
      "headers": { "Authorization": "Bearer YOUR_ANYSEARCH_KEY" }
    }
  }
}
```

Two things I got wrong the first time. The endpoint path is `/mcp`, not `/`. And
if you put this behind nginx, disable response buffering (`proxy_buffering off;`)
or the SSE frames arrive in one lump and the client looks frozen.

## Running several search backends

You can register more than one server. Names must be unique.

```json
{
  "mcpServers": {
    "anysearch": {
      "command": "anysearch-mcp",
      "args": ["--transport", "stdio"],
      "env": { "ANYSEARCH_API_KEY": "YOUR_ANYSEARCH_KEY" }
    },
    "anysearch-eu": {
      "command": "anysearch-mcp",
      "args": ["--transport", "stdio", "--region", "eu"],
      "env": {
        "ANYSEARCH_API_KEY": "YOUR_ANYSEARCH_KEY",
        "ANYSEARCH_BASE_URL": "https://eu.api.anysearch.dev"
      }
    }
  }
}
```

Tool names are namespaced by the client, usually as `anysearch__search` and
`anysearch-eu__search`. The exact separator is client-specific, so check
`list_tools` rather than assuming.

## Debugging the wire

Set `ANYSEARCH_LOG_LEVEL=DEBUG` and watch stderr. MCP logs go to stderr
specifically so they don't corrupt stdio.

```bash
ANYSEARCH_LOG_LEVEL=DEBUG anysearch-mcp --transport stdio 2>mcp.log
```

Then drive it by hand if you need to. Write one JSON-RPC line, read one back:

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"manual","version":"0"}}}' \
  | anysearch-mcp --transport stdio
```

You should get back a `serverInfo` block. If you get nothing, the process died
before it could respond and the traceback is on stderr.

## Timeouts, from three places

This bites people. There are three timeouts and the smallest one wins:

1. The MCP client's request timeout (Claude Desktop is 60s by default).
2. `ANYSEARCH_TIMEOUT` on the HTTP call.
3. Your HTTP client's own socket timeout, if you wrapped anything.

If a tool call hangs for exactly 60s and then fails, it's #1, not AnySearch. You
can't raise that from the server side; look in the client's settings.

## Protocol version

The server advertises `2024-11-05` and negotiates down if the client is older.
If you pin a protocol version in a client that the server doesn't support,
`initialize` fails with a message about no common version. Don't pin unless you
have a reason. I pinned it once, forgot, and spent a while wondering why a
client upgrade broke everything.
