// AnySearch MCP client using the TypeScript/JS SDK from Node.
//
// Setup:
//   npm install @modelcontextprotocol/sdk
//   export ANYSEARCH_API_KEY=YOUR_ANYSEARCH_KEY
//   node examples/node/usage.mjs "kubernetes pod eviction"
//
// ESM only. If you're on CommonJS, wrap this in an async IIFE and swap the
// import syntax; the SDK itself is dual-published so it works either way.

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const key = process.env.ANYSEARCH_API_KEY;
if (!key) {
  console.error("ANYSEARCH_API_KEY is not set. export it first.");
  process.exit(2);
}

const query = process.argv.slice(2).join(" ") || "model context protocol transports";

const transport = new StdioClientTransport({
  command: process.env.ANYSEARCH_MCP_CMD || "anysearch-mcp",
  args: ["--transport", "stdio"],
  // StdioClientTransport does not inherit the parent env by default in older
  // SDK versions. Spreading process.env is the safe move.
  env: { ...process.env, ANYSEARCH_API_KEY: key },
});

const client = new Client({ name: "anysearch-node-demo", version: "0.1.0" });

try {
  await client.connect(transport);

  const { tools } = await client.listTools();
  console.log(`tools: ${tools.map((t) => t.name).sort().join(", ")}`);

  const res = await client.callTool({
    name: "search",
    arguments: { query, max_results: 3 },
  });

  if (res.isError) {
    // Tool ran, world said no. Auth and rate limits land here.
    const text = res.content?.[0]?.text ?? "unknown error";
    console.error(`search failed: ${text}`);
    process.exit(1);
  }

  // The first text block holds a JSON string. content can also hold images,
  // so filter rather than assuming index 0.
  const block = res.content.find((c) => c.type === "text");
  const payload = JSON.parse(block.text);

  for (const [i, hit] of payload.results.entries()) {
    console.log(`${i + 1}. ${hit.title ?? "(no title)"}`);
    console.log(`   ${hit.url}`);
  }
} catch (err) {
  // connect() throws when the subprocess can't start or the handshake fails.
  // Nine times out of ten it's a PATH problem with the server command.
  console.error(`client error: ${err.message}`);
  process.exitCode = 1;
} finally {
  await client.close();
}
