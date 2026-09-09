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
  --allow-live --no-prompt
```

Do not point this at production.

## Keep the tape

```bash
mcp-arcade receipt receipt.json
```

Receipts are `mcp-arcade.bout/v1` JSON. They are the dataset seed for a later Ollama seat. Labels come from the wire. Operator guesses are not ground truth.
