# Changelog

Roughly Keep a Changelog format. Dates are when I tagged, not when I started.

## [0.4.0] - 2025-04-18

- Added Streamable HTTP transport (`--transport http`). The old SSE transport
  still works but prints a deprecation warning on startup.
- `search` gained a `recency` parameter (`day`/`week`/`month`/`year`).
- Resource template `anysearch://cache/{url_hash}` is now readable. It was
  advertised before it worked, which was my mistake.
- Fixed: `extract` returned `truncated: false` even when it had cut the text at
  `max_chars`. The flag is now accurate. Anyone who trusted it was silently
  losing content.
- `ANYSEARCH_TIMEOUT` is per HTTP request now. It used to be a whole-call budget
  including retries, so a slow first attempt could eat the retries' time.

## [0.3.1] - 2025-03-02

- Retry on 429 now respects `Retry-After` when the server sends it. We used to
  back off on our own schedule and get rate limited again.
- Fixed a crash when `search` got an empty `domains` array. It threw a
  validation error instead of treating it as "no filter".

## [0.3.0] - 2025-02-11

- `get_sub_domains` tool. Passive sources only.
- `ANYSEARCH_BASE_URL` is honored again. It regressed in 0.2.0 and nobody
  noticed for three weeks because everyone uses the default.
- Tool errors now come back as `isError: true` with a text body instead of
  JSON-RPC error objects, so clients can tell "bad call" from "bad world". This
  is a behavior change; if you were string-matching on the old shape, update.

## [0.2.0] - 2025-01-09

- Rewrote on `mcp>=1.0` after the 2024-11-05 spec freeze.
- `extract` tool.
- `ANYSEARCH_MAX_RETRIES` and `ANYSEARCH_LOG_LEVEL`.

## [0.1.0] - 2024-12-20

- First working version. `search` only, stdio only.
- Known issue at the time: no session handling, so a client that reconnected
  leaked the old subprocess. Fixed in 0.2.0.
