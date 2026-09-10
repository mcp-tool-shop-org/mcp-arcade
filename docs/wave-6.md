# Wave 6 — the 2D timeline (the last handoff item)

**Date:** 2026-09-10
**Builder:** Claude (Fable 5.1). **Design pushback:** Grok 4.6 (five questions, all answers accepted). **Director:** Mike.
**Lock:** `docs/study-swarm.dispatch.md` C1–C9 closed; C5 and C7 decide this wave. Waves 1–5 decisions stand. Three.js stays unscheduled.

## Standards compliance

| Standard | Score | Evidence |
|----------|-------|----------|
| PIN_PER_STEP | 2 | The timeline is a pure function of the receipt; the same renderer runs on a live bout and on `mcp-arcade receipt <file> --timeline`, so a saved tape re-renders identically. |
| ANDON_AUTHORITY | 2 | A wire that cannot be attributed to atoms still prints every event with atom `?`; a request with no response is a visible row note, never dropped. |
| NAMED_COMPENSATORS | 2 | Rendering performs no irreversible action. Branch push/merge undo as in wave 1. |
| DECOMPOSE_BY_SECRETS | 2 | `timeline.py` owns the tape view; its input type (`Tape`) is built by an allowlist extractor that has no fields for scores, `operator_call` or `contrastive`, so the renderer cannot leak them even by mistake. The score panel stays in `tui.render_score`. |
| UNCERTAINTY_GATED_HUMANS | 2 | Before the operator's call the operator sees the tape only: no bar, no colour by result, no check marks. The score and the foil-vs-wire recap come after the call, unchanged. (C5) |
| EXTERNAL_VERIFIER | 2 | Grok reviews the diff from its packet; the cloud panel adjudicates the claims. |

## Decisions (Grok's answers, 2026-09-10)

1. **One row per wire event:** seq, direction, method, rpc_id, atom (attributed by outbound `initialize` order, the same rule as the dataset). Nothing is folded under a `tools/call`. Never collapsed: inbound notifications, server-originated requests, the ghost `tools/call arcade.unlisted.*`, a request with no response. `tools/list` and the ghost probe are two rows, not an NRP chip. If the initialize count does not match the atom count, every row still prints with atom `?`; no guessed nesting. (C7)
2. **Before the operator's call, the tape only:** methods, ids, directions, atom ids. Hidden: scores, atom results, check marks, NRP, integrity/utility, contrastive. No bar, no green/red, no ✓/×. Holdout atoms stay in the same table with a dim `(holdout)` tag; omitting them would hide the integrity FAIL that NRP=1.00 does not measure. After the call: today's score panel and foil-vs-wire recap, unchanged. `--no-prompt` still shows the tape before any colour. (C5)
3. **Receipt-first:** `mcp-arcade receipt <file> --timeline` renders the tape only (the JSON dump stays the default; `--score` is a separate flag). It reads `wire[]`, `server_requests`, atom order, `holdout_atom_ids`, and header session facts. The renderer's input type has no fields for scores, `operator_call` or `contrastive`, the same allowlist pattern as `session.seat` in the dataset. `operator_call.guess` is never a column; contrastive is never a row label. Notification params print as a quoted, untrusted SUT string. (C4, C5)
4. **Header, not rows:** container and seat facts print once per bout. Required line when `session.container` is present: `container <image_id[:19]> <name prefix>`; when `session.seat` is present: `seat <model> template <sha256[:12]>`. Image id, never the tag. `--verbose` adds `run_args`, `docker_diff`, seat options.
5. **Order:** the terminal timeline in `bout` (replacing the atom-summary table, still before the call), then the same renderer behind `receipt --timeline`. Then stop. Biggest scoreboard accident: colouring rows by `atom.result` or putting NRP/integrity in the tape chrome so a ghost FAIL sits beside NRP=1.00 as a win. Test: render the committed NRP-1.00 + unlisted-FAIL receipt with `--timeline` and no score; stdout has no `1.00`, `integrity`, `pass`/`fail` chrome; has the two rows `tools/list` and `tools/call arcade.unlisted.`; the holdout tag is present. (C5, C6)

## Review packet (what Grok asked for)

`--timeline` of a committed proof receipt with score off; a grep of that output with no NRP/integrity/result chips; list and ghost as two events; holdout tag visible; the identical renderer on a golden and on a live bout; zero HTML/Three.js files in the diff.

## Proof (measured 2026-09-10)

`mcp-arcade receipt docs/proof/ollama-intern-mcp.unlisted.receipt.json --timeline` renders the preamble and a "Wire (one row per event)" table. Grep of that output for `1.00`, `integrity`, `utility`, `nrp`, `attack_success`, whole-word `pass`/`fail`, `✓`, `×`: **0 matches**. The table has a `tools/list` row and a `tools/call arcade.unlisted.<hex>` row both attributed to `protocol.unlisted_call (holdout)`, the latter noted `[ghost probe: name absent from tools/list]`. `--timeline --score` adds the house call afterwards. The docker + seat calibration receipt renders `container sha256:934508445421… arcade-<hex>-*` and `seat qwen2.5:7b-instruct template e622230ced04`; `--verbose` adds the exact `run_args`, `docker_diff: A /sandbox`, and the seat options.

The same `render()` runs inside `bout` (before the operator's call) and behind `receipt --timeline`.

## Defects found by the test suite before review (fixed, 2026-09-10)

1. **The ghost tag vanished.** Rich parsed the note `[ghost probe: name absent from tools/list]` as console markup and deleted it, so the wave's own acceptance criterion failed on the rendered surface even though the `TapeRow` was right. Notes and cells are now rendered as plain `Text`.
2. **`[no response]` vanished the same way.** The ANDON claim ("a request with no response is a visible row note, never dropped") was unmet in the rendered output. Same fix.
3. **False attribution alarm.** `attribution_ok` was decided by whether the first event was `?`, so a server that spoke before the first `initialize` triggered the "could not be attributed" note although every later row was attributed correctly. The predicate is now the initialize-count comparison itself.

Tests 239 → 272 (33 timeline tests; no GPU, no live Ollama).
