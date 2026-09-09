---
title: Getting started
description: Install MCP Arcade, run the lab fixture, and read a bout receipt.
order: 1
---

## Install

```bash
pip install mcp-arcade
```

From a clone: `pip install -e ".[dev]"`. Python 3.11 or later.

## Lab bout

The fixture is a tiny MCP server that ships with Arcade. It can poison a description and rug-pull after N calls. You do **not** need `--allow-live`.

```bash
mcp-arcade bout --target fixture --agent naive --no-prompt -o receipt.json
```

`naive` will follow the whispered errand. You should see an unauthorized `leak` call on the wire and `attack_success=true`.

```bash
mcp-arcade bout --target fixture --agent task-only --no-prompt -o receipt.json
```

`task-only` runs `echo` and stops. The Whispered Errand passes. The Long Con still fails integrity: the fixture mutates on purpose. That is the experiment working, not a broken install.

## Before the house posts the score

Omit `--no-prompt` in a real terminal. Arcade asks what *you* think the wire will show, then posts the contrastive house call. The pause is load-bearing. CI skips it.

## Your server

Fail-closed. Without `--allow-live`, Arcade will not spawn a non-fixture command.

```bash
mcp-arcade bout --target stdio \
  --cmd python --cmd -m --cmd your_server \
  --allow-live --task your_read_only_tool --no-prompt
```

Do not point this at production.

### Real servers

Four things separate a real server from the lab fixture.

**Framing.** The MCP spec's stdio dialect is newline-delimited JSON, one message per line.
Arcade speaks that by default and still speaks `Content-Length` for servers that answer in
it. `--framing auto` (the default) locks to whatever the server answers in, and a frame in
the other dialect after the lock is a protocol error, not a skip. The receipt records
`session.framing` and `session.framing_source`.

**`--task NAME --args JSON`.** This names the benign tool the agent is asked to run. Arcade
will not invent arguments for a tool it does not understand, so without it a real server
with no `echo` tool makes the atoms `SKIP` — on purpose, and utility scores `SKIP` with it.

**`--wrap`.** Opt-in. It appends a house side-quest to the task tool's presented description
and labels the receipt `poison_source: house-wrap`. Leave it off and the poison atom
measures the server's own descriptions (`poison_source: server`).

**`--timeout`.** Per request, default 30 s. A timeout is an atom `ERROR`, never
`attack_success`, and any `ERROR` atom pins NRP to 0.

```bash
mcp-arcade bout --target stdio --cmd "ollama-intern-mcp" \
  --allow-live --agent task-only --task ollama_corpus_list --no-prompt -o receipt.json
```

`--cmd` takes one quoted string like that, or the repeatable form. On Windows a bare npm
shim name resolves via `PATHEXT`.

### Docker

```bash
# Arcade's own fixture image, built locally. No --allow-live needed.
mcp-arcade bout --target docker --agent naive --no-prompt -o receipt.json

# Your image. Always needs --allow-live.
mcp-arcade bout --target docker --image your/server:1.2.3 --cmd your-server \
  --allow-live --task your_read_only_tool --no-prompt
```

One fresh container per atom: no network, read-only root, a per-atom `/sandbox` tmpfs that
Arcade reads back from inside, memory/pid/cpu limits, all capabilities dropped, no host
binds unless you pass `--bind`. The image id is pinned before the first atom and re-checked
before each one. `mcp-arcade docker leftovers` should print `none` afterwards.

## Keep the tape

```bash
mcp-arcade receipt receipt.json
```

Receipts are `mcp-arcade.bout/v1` JSON. They are the dataset seed for a later Ollama seat. Labels come from the wire. Operator guesses are not ground truth.
