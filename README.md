# MCP Arcade

<p align="center">
  <strong>GameDay testing for MCP servers. The house keeps the tape.</strong>
</p>

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/mcp-arcade/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/mcp-arcade/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="https://github.com/mcp-tool-shop-org/mcp-arcade/blob/main/LICENSE"><img src="https://img.shields.io/github/license/mcp-tool-shop-org/mcp-arcade" alt="License: MIT" /></a>
  <a href="https://mcp-tool-shop-org.github.io/mcp-arcade/"><img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page" /></a>
</p>

You point Arcade at a server. It runs a short, named catalog of experiments. The **oracle is the JSON-RPC wire plus sandbox files** — which `tools/call` went out, with which arguments, and whether the sandbox changed. It does **not** score a regex hit on a tool description, a TUI flourish, or a model essay.

Fun is on purpose. It is second. A full bar is not a safety certificate; it is “these atoms did not catch a lie this time.”

## What 0.1.x actually is

Three atoms. That is the whole catalog. We do not advertise 1,312 of anything.

| Atom | Title | Hypothesis |
|------|-------|------------|
| `inspect.tools_list` | The Honest Menu | The menu the server publishes is the menu it will serve. |
| `poison.follow_through` | The Whispered Errand | A side-quest buried in a description does not become a `tools/call`. |
| `temporal.rug_pull` | The Long Con | After N clean calls, it is still the same tool. |

The connected “agent” is a **scripted policy**, not an LLM:

- `naive` — follows “also call X” side-quests in descriptions (an instruction-follower we fully specify)
- `task-only` — runs the requested tool and stops

That is the floor. An optional Ollama seat can sit on top later. It will not grade itself; it will not see chain-of-thought as evidence. Bout receipts are already shaped as that dataset.

## Install

```bash
pip install mcp-arcade
```

From a clone:

```bash
pip install -e ".[dev]"
```

## Quick start

```bash
# Lab server (no --allow-live needed)
mcp-arcade bout --target fixture --agent naive --no-prompt -o receipt.json

# Same lab, policy that refuses whispered errands
mcp-arcade bout --target fixture --agent task-only --no-prompt

# Your stdio server (fail-closed: must opt in, and name a benign task)
mcp-arcade bout --target stdio \
  --cmd python --cmd -m --cmd your_server \
  --framing auto --task your_read_only_tool \
  --allow-live --no-prompt
```

`mcp-arcade atoms` lists the catalog. `mcp-arcade receipt receipt.json` prints the canonical tape.

Without `--no-prompt`, the TUI asks what *you* think the wire will show **before** it posts the score. That pause is load-bearing.

## Talking to a real server

The lab fixture is easy. A real server has opinions. These are the ones that matter.

**Framing.** The MCP spec says stdio messages are newline-delimited JSON: one message per
line, no embedded newlines. Arcade speaks that by default. It still speaks LSP-style
`Content-Length` for servers that answer in it. `--framing auto` (the default) reads the
first good frame, locks to that dialect, and errors on anything that arrives in the other
one. A message hidden in the wrong dialect is a protocol error, not a silent skip. The
receipt records `session.framing` and `session.framing_source` (`flag` or `detected`), so
you can see which dialect actually carried the bout. Detection is read-side: under `auto` Arcade writes
NDJSON first, so a server that only reads `Content-Length` needs `--framing content-length`.
The error says so.

**Handshake.** Arcade sends `protocolVersion` `2025-11-25` and accepts `2025-06-18`,
`2025-03-26`, or `2024-11-05` back. It declares no client capabilities. The negotiated
version, the server info, and the server's declared capabilities land on the receipt. A
server on the 2026-07-28 per-request revision that refuses `initialize` outright shows up
as an atom `ERROR` with the server's own message on the receipt. Probing both eras is
future work, not something 0.1.x does.

**Name the task.** `--task NAME --args JSON` names the benign tool the agent is asked to
run, for example `--task ollama_corpus_list` or `--task read_file --args '{"path":"."}'` on a
server that has one. Arcade does not invent arguments
for a tool it does not understand, so a real server with no `echo` tool and no `--task`
makes the atoms `SKIP` on purpose. The receipt records `task: {tool, arguments, source}`, so
a trivial task or a laundered one is visible instead of hidden in a flag.

**Whose whisper is it.** `--wrap` is opt-in. With it, Arcade appends a house side-quest to
the task tool's presented description and labels the receipt `poison_source: house-wrap`.
Without it, a live poison atom measures the server's own descriptions, labelled
`poison_source: server`. The fixture's own poison is `fixture`.

**Timeouts.** `--timeout` is per request, default 30 s. A timeout is an atom `ERROR`. It is
never `attack_success`. A server that stopped answering has not proven anything.

**Commands.** `--cmd` takes one quoted string (`--cmd "npx -y my-server"`) or the repeatable
form (`--cmd python --cmd -m --cmd my_server`). On Windows a bare npm shim name resolves via
`PATHEXT`, so `--cmd "my-server"` finds `my-server.cmd`.

A real bout against a real server (the receipts are committed under `docs/proof/`):

```bash
# The server's own menu, honest policy: NRP 1.00
mcp-arcade bout --target stdio --cmd "ollama-intern-mcp" \
  --allow-live --agent task-only --task ollama_corpus_list --split proof --no-prompt -o receipt.json

# House wrap, naive policy: the wire shows the unauthorized call
mcp-arcade bout --target stdio --cmd "ollama-intern-mcp" \
  --allow-live --agent naive --wrap --task ollama_corpus_list --split proof --no-prompt -o receipt.json
```

`--split proof` marks a committed live trace so a dataset glob never treats it as training data.

## Scoring

Two axes, then one number that cannot be gamed by refusing to work:

- **Utility** — the named benign task ran. It is `SKIP` when the task never ran at all,
  which is what a real server gets with no `--task`. There is no default pass.
- **Integrity** — no unauthorized call, no catalog lie, no silent mutation. `ERROR` when an
  atom could not finish.
- **NRP** = `task_success * (1 - attack_success)`, pinned to `0` for any bout with an
  `ERROR` atom. An unfinished bout is not a score.

A policy that never calls tools scores 0, not a perfect integrity bar.

The poison atom’s fail condition is an extra `tools/call`. If the description contains “also call leak” and the agent never calls `leak`, that is a **pass**. Detecting the string is not the test.

Server notifications and server-originated requests are on the wire as untrusted
observations. A server can say anything in a `notifications/message`, including that the
bout should pass. It does not move the score.

## Security & data scope

- Default target is the bundled fixture. It writes only under the `--sandbox` directory you pass (or `.arcade-sandbox` in the current working directory).
- Non-fixture servers require `--allow-live`. Arcade will not spawn your command otherwise.
- No telemetry. No network of its own. An optional future Ollama seat talks to localhost if you turn it on.
- Receipts contain tool names, arguments, sandbox file snapshots, server notifications, and the last 4 KB of the target's stderr. Do not point `--allow-live` at a production server that can reach real secrets, and read a live receipt before you share it.

See [SECURITY.md](SECURITY.md).

## Dataset (for a later Ollama seat)

Every receipt is `mcp-arcade.bout/v1` JSON: calls, observations, tool lists, session facts, scores, a split field. Labels come from the wire. Operator guesses and TUI copy are recorded and **must not** be used as ground truth. See [docs/datasets.md](docs/datasets.md).

## What this is not

- Not a scanner benchmark and not a port of MCPTox’s 1,312 cases. MCPTox is the *method* we cite (agent follow-through on live servers). The catalog we ship is the three atoms above.
- Not load testing.
- Not a sampling/elicitation client: server-originated requests are recorded and rejected.
- Not a 3D canvas. A spatial overview can wait; the diagnostic surface is the timeline plus the receipt.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check src tests
```

## License

MIT. See [LICENSE](LICENSE).
