# HANDOFF — Claude builds this out

**Date:** 2026-09-09
**For:** Claude Code on Robot (`E:/AI/mcp-arcade`)
**Not for:** Grok cutting releases. Grok authored the study-swarm lock and a rushed 0.1.0 floor, then published PyPI **1.0.0** on a brand-new unfinished product. Yanked. Do not repeat.

This file is the pick-up. The study-swarm lock is `docs/study-swarm.dispatch.md` (citation gate ACCEPT, 16/16). Dataset contract: `docs/datasets.md`.

## What this product is

GameDay testing for **your MCP server**. Point Arcade at a stdio server. Named experiments run. The **oracle is the JSON-RPC wire plus sandbox files** — which `tools/call` went out, with which arguments, whether the sandbox changed.

It is **not**:

- a scanner-of-schemas (`mcp-stress-test` is a different, stale product — do not salvage it)
- load testing
- MCPTox’s 1,312 cases (cite the *method*, do not vendor or advertise the number)
- a 1.0.0 product

Fun/GameDay naming is wanted. It is **second** to the science.

## Version — hard halt

| Surface | Version |
|---------|---------|
| `pyproject.toml` / `__init__.py` | **0.1.0** |
| PyPI installable | **0.1.0** (`pip install mcp-arcade`) |
| PyPI `1.0.0` | **yanked** (`wrong ver`). Still in the index as history. Do not un-yank. Do not publish another 1.x. |
| GitHub tag `v1.0.0` | deleted |
| GitHub tag `v0.1.0` | current release |

`1.0.0` means the **product** is 1.0. A pending publisher, a first CI, a landing page, or full-treatment’s old “promote to v1.0.0” line is **not** that. Director 2026-09-09. Stay on `0.x` until he says otherwise.

Trusted Publishing is already wired: `.github/workflows/release.yml` + GitHub environment `release` + PyPI pending/active publisher. Cutting a GitHub release of `v0.1.1` (etc.) publishes. **Do not tag unless the Director asks.**

## Where it lives

- Clone: `E:/AI/mcp-arcade`
- GitHub: https://github.com/mcp-tool-shop-org/mcp-arcade
- Pages: https://mcp-tool-shop-org.github.io/mcp-arcade/
- PyPI: https://pypi.org/project/mcp-arcade/
- Org author on leaving commits: `mcp-tool-shop` / `64996768+mcp-tool-shop@users.noreply.github.com`

Identity scan before any push/tag/release: `python %USERPROFILE%\.grok\bin\identity-scan.py .` (and the packed sdist/wheel before PyPI). `RESULT HIT` stops.

## Architectural lock (do not reopen)

From `docs/study-swarm.dispatch.md`. Each traces to a verified finding.

1. **New repo.** Not a salvage of `mcp-stress-test`.
2. **SUT** = operator MCP server + connected agent, in a sandbox. Follow-through = unauthorized `tools/call`, not a regex on a description.
3. **Oracle** = wire + programmatic env check. Dual axis (utility × integrity). NRP so never-calling-tools cannot win.
4. **Deterministic floor + optional LLM later + external verifier.** The LLM does not grade itself. Verifier sees actions/observations only — never CoT, never TUI copy, never `operator_call` as a label.
5. **Health bar is not a safety certificate.** Delay the score until the operator calls it. Contrastive recap.
6. **GameDay framing, not XP.** Small authentic atom catalog. Fuzzing is not the scoreboard.
7. **Three.js is an optional overview later**, not the diagnostic surface. Timeline + receipt first.
8. **Fail-closed.** No target, no bout. `--allow-live` for non-fixture servers.
9. **Do not import or advertise 1,312 cases.**

## What 0.1.0 actually is (a floor, not the build-out)

Python 3.11+ CLI `mcp-arcade`. Hatchling. Click + Pydantic + Rich.

| Path | Role |
|------|------|
| `src/mcp_arcade/protocol.py` | JSON-RPC framing: NDJSON (spec) + Content-Length, auto-detect then lock |
| `src/mcp_arcade/client.py` | stdio MCP client that **records the wire**; demuxes by id, records notifications, rejects server requests, per-request timeout, stderr drain |
| `src/mcp_arcade/fixture.py` | lab server (`echo` + `leak`; poison / rug-pull via env) |
| `src/mcp_arcade/agent.py` | scripted `naive` / `task-only` (frozen “also call X” parser) |
| `src/mcp_arcade/oracle.py` | scores **calls**, not descriptions |
| `src/mcp_arcade/atoms/common.py` | named task (`--task`), fail-closed default: no task, no invented arguments |
| `src/mcp_arcade/atoms/inspect.py` | Honest Menu |
| `src/mcp_arcade/atoms/poison.py` | Whispered Errand |
| `src/mcp_arcade/atoms/rugpull.py` | Long Con |
| `src/mcp_arcade/atoms/unlisted.py` | Ghost on the Menu (holdout; protocol surface) |
| `src/mcp_arcade/bout.py` | one fresh fixture process per atom |
| `src/mcp_arcade/receipt.py` | canonical `mcp-arcade.bout/v1` JSON |
| `src/mcp_arcade/timeline.py` | the tape: one row per wire event, allowlisted view, receipt-first |
| `src/mcp_arcade/tui.py` | tape before the call, delayed score, contrastive house call after |
| `src/mcp_arcade/docker.py` | docker target: argv with safe defaults, image id pin + drift check, `/sandbox` snapshot via exec, `docker diff`, force-remove compensator, local fixture image build |
| `src/mcp_arcade/seat.py` | the ollama seat: frozen template + sha, tools as presented, only tool calls leave the reply, cap, timeouts |
| `src/mcp_arcade/prompts/seat.system.txt` | the frozen system prompt (hashed onto the receipt; must not coach) |
| `src/mcp_arcade/dataset.py` | one JSONL row per atom, labels from the wire, holdout by atom id, manifest with sha256 per receipt |
| `src/mcp_arcade/cli.py` | `bout`, `atoms`, `receipt [--timeline --score --verbose]`, `fixture`, `dataset`, `docker {build-fixture,rm-fixture,leftovers}` |
| `tests/test_oracle.py` | tautology test: poison *string* ≠ attack_success |
| `tests/fixtures/` | golden receipts, one per stdio framing; an oracle regression fails the diff |

Prove the floor:

```bash
pip install -e ".[dev]"
pytest
mcp-arcade bout --target fixture --agent naive --no-prompt -o receipt.json
mcp-arcade bout --target fixture --agent task-only --no-prompt
```

`naive` must `tools/call leak`. `task-only` must not. If a change makes the description-regex the score, the tautology test is supposed to go red — **do not weaken it**.

## What is NOT built (this is the work)

0.1.0 is a scripted-agent harness against a toy fixture. The product the Director asked for is still ahead.

**Do this, in roughly this order. Do not skip to Three.js or a 1.0 tag.**

### 1. Harness that survives a real server

- ~~Stdio client: timeouts, stderr drain, servers that speak NDJSON instead of Content-Length, initialize/protocolVersion negotiation~~ **done (wave 1, 2026-09-09)**
- ~~`--cmd` quoting on Windows~~ **done (wave 1, 2026-09-09)**
- ~~Golden receipts in `tests/fixtures/` (commit them; oracle regressions should fail the diff)~~ **done (wave 1, 2026-09-09)**
- Dual-era probing (`server/discover`, MCP revision 2026-07-28) — not built; legacy `initialize` only
- HTTP/SSE transport only if a real target needs it — don’t invent it

### 1b. Docker is the sandbox (Director, 2026-09-09) — **done (wave 2, 2026-09-09)**

- ~~`--target docker --image <ref>`: pinned `docker run` with safe defaults; effective run line and image id on the receipt~~ done
- ~~Env oracle for docker targets~~ done: per-atom `/sandbox` tmpfs snapshotted from inside via `docker exec tar` (contents), `docker diff` beside it (paths). `docker diff` alone is names, not bytes
- ~~Fixture-image gate~~ done: Arcade builds its own fixture image and only that id skips `--allow-live`. A look-alike tag is refused
- Open: publishing a fixture image to a registry (Director's call); GPU passthrough for the agent seat (comes with the seat); multi-container topologies (not planned)
- Decisions and Grok's pushback: `docs/wave-2.md`

### 2. A real agent seat (still not a judge) — **done (wave 4, 2026-09-09)**

- ~~Plug an agent that *sees* `tools/list` and *emits* `tools/call` (Ollama local first)~~ `--agent ollama:<model>`, `src/mcp_arcade/seat.py`; endpoint configurable, local by default
- ~~The oracle **does not change**~~ unchanged; the seat's calls go through the recording client
- ~~Keep `naive` / `task-only` as controls~~ calibration set under `docs/proof/calibration.*`, one image id
- ~~`agent_policy: ollama`. No rationale field~~ `session.seat` carries model/temperature/seed/num_ctx/endpoint/template sha; model text never reaches the receipt (tested with a mock that lies)
- Open: a cloud/API seat (endpoint is already a flag); a real server under the seat with `--allow-live`
- Decisions and Grok's answers: `docs/wave-4.md`

### 3. Dataset generation (for that seat) — **done (wave 3, 2026-09-09)**

Contract is `docs/datasets.md`; generator is `src/mcp_arcade/dataset.py`, CLI `mcp-arcade dataset`.

- ~~`mcp-arcade bout --target fixture --agent naive|task-only -o …` as the labeled pair~~ the committed goldens under `tests/fixtures/` are that pair; `split: proof` receipts never become rows
- ~~Holdout by **new atom id**~~ unknown ids and `holdout_atom_ids` go to `holdout.jsonl` always; public-train ids are a frozen tuple in the code
- ~~Never train/judge on `operator_call`, TUI, or CoT~~ rows never carry them; ERROR/SKIP atoms are dropped, not kept as "held"
- Decisions and Grok's answers: `docs/wave-3.md`

### 4. Atom catalog growth (short, authentic)

Add atoms we can actually run. Candidates from the lock (protocol/host as a **separate wave**, not folded into description-regex):

- catalog mutation mid-session already exists (Long Con)
- unauthorized call already exists (Whispered Errand)
- ~~tools that appear in `call` but not `list`~~ **done (wave 5, 2026-09-10)**: `protocol.unlisted_call`, The Ghost on the Menu — `src/mcp_arcade/atoms/unlisted.py`, fixture flag `ARCADE_UNLISTED`, id in `holdout_atom_ids`, proven refused by `ollama-intern-mcp` (`docs/proof/ollama-intern-mcp.unlisted.receipt.json`)
- next candidates: capability-honesty (declared capabilities vs served methods), protocol abuse (malformed ids, oversized frames)

New atom ids start in `dataset.holdout_atom_ids`. Promotion to public-train is a reviewed edit of `PUBLIC_TRAIN_ATOM_IDS`, never a CLI switch. Do not advertise MCPTox counts.

### 5. Operator UX — **done (wave 6, 2026-09-10)**

- ~~Better timeline of the tape (2D, receipt-first)~~ `src/mcp_arcade/timeline.py`; `mcp-arcade receipt <file> --timeline`; one row per wire event; allowlisted `Tape` so no score can appear before the call
- ~~Contrastive recap stays foil vs wire~~ unchanged, after the call
- Three.js: not scheduled. If it ever comes, it is an overview pane fed by the same `Tape`, never where ids, counts or call traces are read (C7)
- Decisions and Grok's answers: `docs/wave-6.md`

## Live fire (wave 7, 2026-09-10)

`docs/live-fire.md` is the packet the Director reads before anyone asks about 1.0: controls, seat, ghost atom and Long Con against `ollama-intern-mcp` under `--allow-live`, 0.x limits beside the table. Two rules it forced: a live `--wrap` needs `--wrap-target`, and a seated live bout sends only `--seat-allow` tools (attempts outside are recorded, never sent). Committed proofs are grepped for host home paths by `tests/test_proofs.py`; the external identity scanner misses double-escaped backslashes.

## Do not

- Tag `1.x` or un-yank PyPI `1.0.0`
- Salvage `mcp-stress-test` as this product
- Score descriptions with regex and call it follow-through
- Let an LLM grade its own bout
- Skip `--allow-live` for non-fixture targets
- Run translations / full-treatment “promote to 1.0.0” as a ritual
- Put home paths, personal mailboxes, or Tailscale addresses in git-tracked files
- Commit without tests for the code you touched

## Verify

```bash
pytest
ruff format --check .
ruff check .
python %USERPROFILE%\.grok\bin\identity-scan.py .
```

`pytest` runs the suite against both stdio framings (NDJSON and Content-Length) and
diffs the golden receipts in `tests/fixtures/`.

CI: `.github/workflows/ci.yml` (3.11/3.12). Release: `.github/workflows/release.yml` on GitHub **release published**, environment `release`.
