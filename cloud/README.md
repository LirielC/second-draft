# Second Draft — hosted adapter

A Worker-compatible TypeScript implementation of the Second Draft MCP workflow, plus a private English-language React gallery.

The Python server remains at the repository root. This adapter uses Cloudflare D1 instead of local SQLite; their records are not automatically synchronized.

## Features

- Stateless MCP JSON-RPC endpoint at `/mcp`.
- The same five named tools as the Python server.
- Per-user data isolation using trusted hosting identity headers.
- Prepared SQL queries and atomic revision-checked updates.
- Project gallery, archive form, and Remix source brief.
- Generated Drizzle schema migrations.

## Development

Requires Node.js 22.13+ and pnpm.

```bash
cd cloud
pnpm install --frozen-lockfile
pnpm exec tsc --noEmit
pnpm run build
```

Hosted deployment requires a Sites project with `mcp` capability and a D1 binding named `DB`. The reusable `.openai/hosting.json` intentionally omits the original deployment's project ID. Register a new project before deploying your own copy.

D1 schema changes belong in `db/schema.ts`. Generate migrations using `pnpm run db:generate`, inspect the SQL, and deploy with the migration metadata. Do not edit applied migrations.

## Authentication

The hosting boundary handles OAuth and private access. Data-bearing MCP and API operations additionally require `oai-authenticated-user-id`. That header is trusted only behind the configured hosting boundary. Do not deploy this adapter to a server that accepts arbitrary client-supplied identity headers.

Discovery returns tool definitions only; it never exposes project records. API writes require a matching request origin. User-scoped queries and revision checks protect updates.

## Gallery workflow

1. Archive a project with its original idea, reason for pausing, and reusable pieces.
2. Search or browse the archive.
3. Select 2–5 projects, provide a goal and hour budget, then prepare the brief.
4. Copy the brief into ChatGPT, or use the connected MCP tools in the conversation.

The brief contains recorded evidence. The web UI does not call an AI model or generate a project proposal.
