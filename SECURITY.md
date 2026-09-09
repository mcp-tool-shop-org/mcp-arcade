# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | yes       |

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
- No outbound network in v1 (stdio subprocess only)
- Sandbox writes stay under `--sandbox`
- The fixture `leak` tool writes a token file inside that sandbox on purpose — that is the env oracle, not exfiltration to the network
