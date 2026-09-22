# Driving the HTTP transport with curl

When a client misbehaves, I drop to curl. It removes every layer of guessing.
This walks the full Streamable HTTP handshake by hand. Copy the blocks in order.

Start the server somewhere you can see stderr:

```bash
anysearch-mcp --transport http --host 127.0.0.1 --port 8765
```

## 1. Initialize

The `Accept` header must list both types. If you send only `application/json`
the server replies `406 Not Acceptable`, because a single request may legally
answer with either a JSON body or an SSE stream.

```bash
curl -i -sS http://127.0.0.1:8765/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "curl", "version": "0.0.1"}
    }
  }'
```

Response headers matter here. Look for `Mcp-Session-Id`:

```
HTTP/1.1 200 OK
content-type: application/json
mcp-session-id: 6f1c2a4e-9b77-4d0a-8f31-2c5e0d9a71bb

{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{},"resources":{}},"serverInfo":{"name":"anysearch-mcp","version":"0.4.0"}}}
```

If there is no `Mcp-Session-Id`, the server is running stateless and you can
skip the next step. Older builds always issued one.

## 2. Tell the server you're ready

A notification (no `id`, no response body expected). Forgetting this step is why
people see "server not initialized" on the next call.

```bash
SID=6f1c2a4e-9b77-4d0a-8f31-2c5e0d9a71bb

curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8765/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "Mcp-Session-Id: $SID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

Expect `202`. Anything else means the session id is wrong.

## 3. List tools

```bash
curl -sS http://127.0.0.1:8765/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "Mcp-Session-Id: $SID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | jq '.result.tools[].name'
```

```
"extract"
"get_sub_domains"
"search"
```

If `jq` prints nothing, pipe to `head -c 500` instead. You probably got an error
object and `jq` silently returned null.

## 4. Call a tool

```bash
curl -sS http://127.0.0.1:8765/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "Mcp-Session-Id: $SID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "search",
      "arguments": {"query": "mcp streamable http", "max_results": 2}
    }
  }' | jq -r '.result.content[0].text' | jq .
```

That double `jq` is not a typo. The result is JSON-RPC wrapping a text block
whose body is itself a JSON string. First pass unwraps the protocol, second
unwraps the tool payload.

## When it answers with SSE

If the response `content-type` is `text/event-stream`, you get framed events:

```
event: message
data: {"jsonrpc":"2.0","id":3,"result":{...}}
```

curl handles it fine, you just have to read past the `event:`/`data:` lines.
Strip them:

```bash
... | sed -n 's/^data: //p' | jq -r '.result.content[0].text'
```

## Common failures

| What you see | Cause |
| --- | --- |
| `406 Not Acceptable` | Missing `text/event-stream` in `Accept` |
| `400` "session not found" | Wrong or stale `Mcp-Session-Id` |
| `401` `{"error":"unauthorized"}` | Server started without `ANYSEARCH_API_KEY` |
| `-32601 method not found` | Typo in `method` or tool name |
| Connection reset, no body | Server crashed; check its stderr |

## Tearing down

```bash
curl -sS -X DELETE http://127.0.0.1:8765/mcp -H "Mcp-Session-Id: $SID"
```

Not every server implements DELETE. If you get a 405, it just lets sessions
expire. Mine does.
