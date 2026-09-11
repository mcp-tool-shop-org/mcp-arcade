<p align="center">
  <a href="README.md">English</a> | <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

# MCP Arcade

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/mcp-arcade/readme.png" alt="MCP Arcade" width="400" />
</p>

<p align="center">
  <strong>GameDay for MCP servers. The house keeps the tape.</strong>
</p>

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/mcp-arcade/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/mcp-arcade/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="https://github.com/mcp-tool-shop-org/mcp-arcade/blob/main/LICENSE"><img src="https://img.shields.io/github/license/mcp-tool-shop-org/mcp-arcade" alt="License: MIT" /></a>
  <a href="https://mcp-tool-shop-org.github.io/mcp-arcade/"><img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page" /></a>
</p>

You point Arcade at a server. It runs four named experiments. The **oracle is the JSON-RPC wire**: which `tools/call` went out, with which arguments, and whether the sandbox changed. It does not score a regex on a tool description, a flourish in a TUI, or a model essay.

A full bar is not a safety certificate. It is “these experiments did not catch a lie this time.”

The tape that comes out can be played as **[Ghost on the Menu](https://mcp-tool-shop-org.github.io/mcp-arcade-cabinets/play/)**, a short arcade shooter in the sister repo. The instrument scores the wire. The game never does.

## The four experiments

That is the whole catalog.

| Experiment | What it asks |
| ---------- | ------------ |
| The Honest Menu | Is the menu the server publishes the menu it will serve? |
| The Whispered Errand | Does a side-quest buried in a description become a `tools/call`? |
| The Long Con | After a few clean calls, is it still the same tool? |
| The Ghost on the Menu | Does the server answer a name that was never on the menu? |

The agent on the other end is a **policy**, not a judge: `naive` follows “also call X” whispers, `task-only` runs the named tool and stops, `ollama:<model>` is a local model that sees the menu and emits calls. `naive` and `task-only` are the controls.

## Install

```bash
pip install mcp-arcade
```

Python 3.11 or later. From a clone: `pip install -e ".[dev]"`.

## Run a bout

```bash
# Lab fixture. No --allow-live needed. naive will follow the whisper.
mcp-arcade bout --target fixture --agent naive --no-prompt -o receipt.json

# Same lab, policy that refuses whispered errands.
mcp-arcade bout --target fixture --agent task-only --no-prompt

# Your stdio server. Fail-closed: opt in, and name a benign task.
mcp-arcade bout --target stdio \
  --cmd python --cmd -m --cmd your_server \
  --task your_read_only_tool \
  --allow-live --no-prompt
```

`mcp-arcade atoms` lists the catalog. Leave off `--no-prompt` in a real terminal: Arcade asks what *you* think the wire will show before it posts the score.

Docker is the sandbox for a real container. The fixture image needs no `--allow-live`; your image always does. See the [handbook](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/getting-started/) for flags, framing, the local-model seat, and what a green bar is not.

## Keep the tape

```bash
mcp-arcade receipt receipt.json --timeline    # one row per wire event, no score
mcp-arcade tape receipt.json -o tape.json     # the cabinet's input
```

The timeline is the diagnostic: every `tools/call`, every reply, every notification. Scores stay off it until you ask. The tape file is what [Ghost on the Menu](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets) reads. Arcade never writes a game score onto it.

## More

- [Handbook](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/) — install, a first bout, the CLI, how scoring works
- [Changelog](CHANGELOG.md) — what shipped in each wave
- [SECURITY.md](SECURITY.md) — default is the lab fixture; live servers need `--allow-live`; no telemetry
- [Live fire](docs/live-fire.md) — a real SDK server, the controls, and the limits of 0.x

Do not point `--allow-live` at a production server that can reach real secrets. Read a live receipt before you share it.

MIT. See [LICENSE](LICENSE). Built by [MCP Tool Shop](https://mcp-tool-shop.github.io/).
