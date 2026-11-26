# ADR-0020: Local API Token

**Status:** Adopted

**Context:**

RIP's REST API can read repository files, run indexing, and apply edits, which runs a project's validation commands. Before this decision it had three protections: it listened only on `127.0.0.1`, it accepted only local `Host` headers (DNS rebinding), and CORS limited browser requests to the RIP app. FastAPI also refuses non-JSON bodies, which blocks cross-site form posts.

That still left the API open to any process on the machine, including processes of other user accounts on a shared computer, and to anything that could reach it if someone set `LOC_SERVER_HOST=0.0.0.0`. It also undercut the MCP server's `--editing propose` mode: an agent limited to proposing over MCP, but able to run shell commands, could call `POST /editing/proposals/{id}/apply` itself.

**Decision:**

- Every REST request except `GET /api/v1/health` must send `Authorization: Bearer <token>`; otherwise it gets HTTP 401 before any handler runs. `/health` stays open, so the app can tell "backend not running" apart from "not signed in".
- The token is created on first use with `secrets.token_urlsafe(32)` in a per-user file, `~/.local_openclaw/api.token` (mode 0600 where supported; `LOC_API_TOKEN_PATH` overrides the location). It is compared in constant time.
- Like Jupyter, the backend prints a sign-in link at startup (`open_this_link=http://localhost:5173/?token=…`, base URL from `LOC_SERVER_FRONTEND_URL`). Opening it stores the token in the app and removes it from the address bar. The app can also take a pasted token.
- The app streams chat with `fetch` instead of `EventSource`, because `EventSource` cannot send headers, and a token in the URL would be written to server access logs.
- The MCP server is unaffected: it talks over stdio, and its agent was started by the user.

**Consequences:**

Positive:
- Processes of other user accounts, and anything reaching an accidentally exposed port, can no longer use the API.
- Calling the API from an agent becomes a deliberate act (reading a secret file outside the repository), which agent permission rules can forbid; see the MCP server guide.

Negative:
- A process running as the same user can read the token file. **The token does not stop such a process**; it only makes the attempt explicit. Real enforcement against a user's own agents belongs to the agent's sandbox and permission settings.
- The sign-in link appears in the backend's console output (and in its logs if they are kept). Anyone who can read them already runs as the user.
- The app must be signed in once per browser profile, and again if the token file is deleted.

**Alternatives Considered:**

- No token, relying on agent permission rules alone: rejected; it leaves the API open to other user accounts.
- The Vite dev proxy injecting the token: rejected; the proxy on `localhost:5173` would itself become an unauthenticated way into the API.
- A token in the query string for streaming: rejected; query strings are logged.
