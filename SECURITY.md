# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | yes       |

## Reporting

Do not file a public GitHub issue for a vulnerability in MCP Arcade itself.

Open a private GitHub security advisory on `mcp-tool-shop-org/mcp-arcade`.

Include what broke, how to reproduce, and impact. We will acknowledge within 48 hours.

## Responsible use

MCP Arcade is a GameDay harness. It talks to MCP servers you name.

**Do**

- Run `--target fixture` in a throwaway directory
- Pass `--allow-live` only for servers you own, in a sandbox
- Treat bout receipts as sensitive if the target saw real arguments

**Do not**

- Point `--allow-live` at production
- Use Arcade to attack servers you do not operate
- Treat a passing NRP as a certification

## Data scope

- No telemetry
- No outbound network of its own (stdio subprocess only)
- Sandbox writes stay under `--sandbox`
- The fixture `leak` tool writes a token file inside that sandbox on purpose — that is the env oracle, not exfiltration to the network
- A docker target runs each atom in its own container with no network, a read-only root, a per-atom tmpfs sandbox, memory/pid/cpu limits, all capabilities dropped, and no host bind mounts unless you pass `--bind` (recorded on the receipt). Arcade force-removes every container it started
- `--image` always requires `--allow-live`. Only the fixture image Arcade builds itself, verified by image id, skips it

### What a receipt holds

A receipt is the tape. It records what the harness observed, because the verifier is
allowed to see actions and observations and nothing else. That means a receipt now also
contains:

- **Server notifications** — anything the target pushed on the wire (`notifications/*`),
  recorded verbatim. They are observations, not labels; the oracle never scores their text.
- **Server-originated requests** — `sampling/createMessage`, `elicitation/create`,
  `roots/list`, `ping`. Arcade records them, answers with a JSON-RPC error, and lists them
  as `server_requests`.
- **The negotiated protocol version and server info** — what the server answered to
  `initialize`, plus its declared capabilities.
- **A stderr tail** — the last 4 KB the target wrote to stderr, as `session.stderr_tail`.
  It is kept so a failed handshake has a cause instead of a shrug.

A stderr tail contains whatever the target chose to log: paths, tokens, request bodies,
anything. Arcade does not filter it. **Treat receipts from live targets as sensitive**,
and read one before you attach it to an issue or a dataset.
