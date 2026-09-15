---
title: The tape
description: What a tape is, what it may carry, how to export one from a bout, and how the arcade plays it.
order: 3
---

A **receipt** is everything Arcade knows about a bout: the wire, the scores, your pre-score call, the contrastive recap, the sandbox snapshots. A **tape** is the allowlisted view of a receipt: the wire, in order, and nothing that judges it. The instrument scores the wire; everything downstream reads the tape.

## What is on it

`mcp-arcade tape receipt.json -o tape.json` writes `mcp-arcade.tape/v1` JSON:

- **Header words.** The bout id, the target kind (fixture, stdio or docker), the agent policy, the framing, the protocol version, the server's name, the container image if there was one, the seat's model and template hash if a model sat.
- **Atoms.** One entry per experiment, with its id, the named task tool, and whether it is a holdout atom.
- **Rows.** One per wire event: sequence, direction, method, JSON-RPC id, the atom it belongs to, and a short note (the tool a `tools/call` named, a `[no response]`, the ghost probe's note). Notifications are quoted as untrusted strings from the server. Server-originated requests are rows of their own.
- **Facts.** One closed word per atom, derived from the wire and nothing else: `followed` or `held` for the whispered errand, `ghost_answered` or `ghost_refused` for the unlisted call, `menu_changed` or `menu_stable` for the long con.

## What is not on it, by construction

The `Tape` type has no field for a score, a result, `attack_success`, NRP, integrity, utility, your `operator_call` or the contrastive recap. The exporter builds the tape from an allowlist, and the consumer side refuses any document that carries one of those keys at any depth. A game or a dataset built on tapes cannot show a verdict it was never given.

## Reading one in the terminal

```bash
mcp-arcade receipt receipt.json --timeline             # the tape, one row per event
mcp-arcade receipt receipt.json --timeline --score     # then the house call, after it
mcp-arcade receipt receipt.json --timeline --verbose   # run_args, docker diff, seat options
```

In a real terminal `bout` shows the timeline before it asks for your call, so you read the wire before the verdict. The pause is load-bearing.

## Playing one

The sister repo [mcp-arcade-cabinets](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets) is an arcade of small games, each built from tapes and nothing else: a cabinet reads header words, rows and facts through a loader that rejects score fields, never loads a receipt, and never talks to a server. Today the arcade has a replay shooter and a typing game; more cabinets will land there, and every one of them reads the same tape.

```bash
npx @mcptoolshop/ghost-on-the-menu     # serves the arcade on your machine
```

Or [play in the browser](https://mcp-tool-shop-org.github.io/mcp-arcade-cabinets/play/). Twenty tapes ship with the arcade, exported by this instrument from the committed proofs and from bouts against the arcade's own MCP server. To play your server, record a bout with `--allow-live`, export the tape, and drop it beside the arcade's fixtures (or hand it to the arcade's container as a read-only volume). Read a live receipt before you share its tape: the header names your server and the tool names are real.

## Recording a server you run

```bash
mcp-arcade bout --target stdio --cmd "npx -y your-server" \
  --task your_read_only_tool --allow-live -o your.receipt.json
mcp-arcade tape your.receipt.json -o your.tape.json
```

Use `--split proof` if the receipt will be committed somewhere a dataset glob could find it; proof receipts yield tapes but never training rows.
