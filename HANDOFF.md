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
| `src/mcp_arcade/protocol.py` | Content-Length JSON-RPC framing |
| `src/mcp_arcade/client.py` | stdio MCP client that **records the wire** |
| `src/mcp_arcade/fixture.py` | lab server (`echo` + `leak`; poison / rug-pull via env) |
| `src/mcp_arcade/agent.py` | scripted `naive` / `task-only` (frozen “also call X” parser) |
| `src/mcp_arcade/oracle.py` | scores **calls**, not descriptions |
| `src/mcp_arcade/atoms/inspect.py` | Honest Menu |
| `src/mcp_arcade/atoms/poison.py` | Whispered Errand |
| `src/mcp_arcade/atoms/rugpull.py` | Long Con |
| `src/mcp_arcade/bout.py` | one fresh fixture process per atom |
| `src/mcp_arcade/receipt.py` | canonical `mcp-arcade.bout/v1` JSON |
| `src/mcp_arcade/tui.py` | delayed score, contrastive house call |
| `src/mcp_arcade/cli.py` | `bout`, `atoms`, `receipt`, `fixture` |
| `tests/test_oracle.py` | tautology test: poison *string* ≠ attack_success |

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

- Stdio client: timeouts, stderr drain, servers that speak NDJSON instead of Content-Length, initialize/protocolVersion negotiation
- `--cmd` quoting on Windows
- Golden receipts in `tests/fixtures/` (commit them; oracle regressions should fail the diff)
- HTTP/SSE transport only if a real target needs it — don’t invent it

### 2. A real agent seat (still not a judge)

- Plug an agent that *sees* `tools/list` and *emits* `tools/call` (Ollama local first; optional API later)
- The oracle **does not change**. Same wire, same NRP
- Keep `naive` / `task-only` as controls
- Receipt field for `agent_policy: ollama` (or similar). No rationale field the judge can see

### 3. Dataset generation (for that seat)

Contract is already `docs/datasets.md`. Build the generator:

- `mcp-arcade bout --target fixture --agent naive|task-only -o …` as the labeled pair
- Holdout by **new atom id**, not by shuffling the public three
- Never train/judge on `operator_call`, TUI, or CoT

### 4. Atom catalog growth (short, authentic)

Add atoms we can actually run. Candidates from the lock (protocol/host as a **separate wave**, not folded into description-regex):

- catalog mutation mid-session already exists (Long Con)
- unauthorized call already exists (Whispered Errand)
- next: protocol abuse / capability-honesty / tools that appear in `call` but not `list`

New atom ids start in `dataset.holdout_atom_ids`. Do not advertise MCPTox counts.

### 5. Operator UX

- Better timeline of the tape (2D, receipt-first)
- Contrastive recap stays foil vs wire
- Three.js **last**, overview only, never where counts are read

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

CI: `.github/workflows/ci.yml` (3.11/3.12). Release: `.github/workflows/release.yml` on GitHub **release published**, environment `release`.
