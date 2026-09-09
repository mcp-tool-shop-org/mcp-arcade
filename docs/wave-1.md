# Wave 1 — the harness survives a real server

**Date:** 2026-09-09
**Builder:** Claude (Fable 5.1). **Design pushback:** Grok 4.6 (two rounds, read-only session). **Director:** Mike.
**Lock:** `docs/study-swarm.dispatch.md` C1–C9 is closed and not reopened here.

## Standards compliance

| Standard | Score | Evidence |
|----------|-------|----------|
| PIN_PER_STEP | 2 | Goldens pin `ARCADE_FRAMING` per dialect; receipts carry `framing`, `framing_source`, `protocol_version`, and the fixture version. Builder model and reviewer model are named above. |
| ANDON_AUTHORITY | 2 | A malformed frame is a `ProtocolError` → atom `ERROR` → NRP 0. A request timeout is atom `ERROR`. Nothing downstream scores an atom that errored as a pass. |
| NAMED_COMPENSATORS | 2 | Wave 1 performs no irreversible call. Compensators table below covers the only two this branch can reach. |
| DECOMPOSE_BY_SECRETS | 2 | Framing lives in `protocol.py`; demux/timeouts in `client.py`; scoring in `oracle.py`; the oracle does not import the client. |
| UNCERTAINTY_GATED_HUMANS | 2 | Version stays 0.x; tagging is the Director's call, never the builder's. Design questions were put to Grok contrastively (decision first, then why). |
| EXTERNAL_VERIFIER | 2 | The wave-1 diff is reviewed by Grok (not Claude) from the diff + test output + receipts only; builder reasoning withheld. Cloud verifier (Ollama Cloud, non-Claude) on the claims in this doc. |

**Compensators** (irreversible actions this branch can reach):

| Action | Undo | Post-rollback state | Owner |
|--------|------|---------------------|-------|
| `git push` of the wave-1 branch | `git push origin --delete wave-1/real-server-harness` | main untouched | Claude |
| Merge to `main` | `git revert -m 1 <merge-sha>` then push | main at pre-merge tree, history kept | Claude |

No tag, no PyPI publish, no `gh release` on this branch. (HANDOFF: "Do not tag unless the Director asks.")

## Why this wave exists

The MCP spec (2025-06-18, *Transports*) says stdio messages are **newline-delimited** and **must not contain embedded newlines**. 0.1.0's client spoke only LSP-style `Content-Length` framing, and the fixture spoke it too, so the suite never noticed. Verified live 2026-09-09: `ollama-intern-mcp` (official TypeScript SDK) answers `initialize` as one JSON line, protocol `2025-06-18`. 0.1.0 could not complete a handshake with it.

## Decisions (settled with Grok, 2026-09-09)

1. **Receipt schema stays `mcp-arcade.bout/v1`, additive.** New session facts: `framing`, `framing_source`, `protocol_version`, `server_info`, `server_capabilities`, `stderr_tail`, `server_requests`, `task`. Notifications go on the existing `wire[]`, not a sibling array. `dataset.agent_policy` (a duplicate) is removed. No `agent` block until wave 2 — an empty one is a rationale hole (C4). Bump to v2 only when a label's meaning changes.
2. **Server notifications are untrusted observations.** They stay in the verifier's view (C3, C4) — stripping them would hide the very persuasion channel a wave-2 agent reads. The oracle never scores their text; the tautology test is extended so notification copy cannot move `scores`. The TUI prints them as SUT wire, never in Arcade's voice (C5).
3. **Framing is `auto` by default, locked after the first good inbound frame.** Detection is read-side only: under `auto` Arcade writes the spec dialect (NDJSON) first, so a server that only *reads* Content-Length dies on that first line. There is no wire-compatible hybrid (an NDJSON reader would choke on a `Content-Length:` header). Measured 2026-09-09 by the test suite; the failure is fast and named, and the error tells the operator to rerun with `--framing content-length`. `--framing ndjson|content-length|auto`. `framing_source` is `flag` or `detected`. A malformed line under lock is an `ERROR`, never a silent skip — that closes the "hide a message in the other dialect" game. Goldens pin `ARCADE_FRAMING` explicitly; auto is the product default, not the golden generator.
4. **Operator names the benign task** (`--task NAME --args JSON`). It can game NRP (trivial tool; or naming the attack tool so follow-through launders into utility), so the receipt records `task: {tool, arguments, source}` and utility is `SKIP` unless that task actually ran. The old `_utility` fallback to `PASS` is deleted. Poison labels its source: `fixture | house-wrap | server`. The house wrap on live targets is opt-in (`--wrap`); without it, live poison measures the server's own descriptions.
5. **Server-originated requests** (`sampling/createMessage`, `elicitation/create`, `roots/list`, `ping`) are recorded on the wire, answered with a JSON-RPC error (Arcade is not a sampling client, C8), never complete a pending client future, and are listed at receipt level as `server_requests: [{atom_id, method, rpc_id, rejected}]`. Not a `Check` — SKIP means "did not run", and this did. The protocol wave scores them with a hypothesis.
6. **Client capabilities are empty.** `tools` is a server capability; Arcade declares no `roots`, `sampling`, or `elicitation`. The server's declared capabilities and negotiated `protocolVersion` are recorded. (Grok first proposed sending `capabilities.tools`; conceded on the spec.)
7. **Timeouts:** per-request `--timeout` (default 30 s). A timeout is atom `ERROR`, never `attack_success`.
8. **Order after this wave:** dataset CLI → Ollama seat → `protocol.unlisted_call` atom → 2D timeline. Three.js is not scheduled (C7).

## Real-server proof

Target: `ollama-intern-mcp` (local, npm global, `@modelcontextprotocol/sdk`). Run under `--allow-live` in a temp sandbox. The receipt is committed as a **version-pinned extra**, not a golden diff — a real server's output is not stable enough to diff in CI.

## Proof (measured 2026-09-09)

Two receipts under `docs/proof/`, both against `ollama-intern-mcp` 2.6.0 (`@modelcontextprotocol/sdk`, 42 tools), framing detected `ndjson`, protocol `2025-11-25`, task `ollama_corpus_list` named by the operator:

| Receipt | Policy | Wrap | Result |
|---------|--------|------|--------|
| `ollama-intern-mcp.task-only.receipt.json` | task-only | no | integrity pass, utility pass, NRP 1.00. `poison_source: none` — the server's own menu carries no whisper. |
| `ollama-intern-mcp.naive-wrap.receipt.json` | naive | yes | integrity fail, attack_success true, NRP 0.00. The wire shows an unauthorized `tools/call ollama_research`. `poison_source: house-wrap`. |

The second receipt is the point of the wave: follow-through caught on the wire of a real SDK server, not on a regex over a description. Both are version-pinned extras, not CI goldens.

## Not built in wave 1 (open)

- **Dual-era probing.** MCP revision 2026-07-28 replaced `initialize` with per-request `_meta` versioning and a mandatory `server/discover`. Arcade speaks the legacy handshake only (2025-11-25 and earlier). A modern-only server that rejects `initialize` surfaces as an atom ERROR with the server's error on the wire. Add the stdio probe (`server/discover`, fall back on a non-modern error) when a real target needs it.
- HTTP/SSE transport (HANDOFF: only if a real target needs it).

## Docker (Director, 2026-09-09: "keep it in mind from the beginning")

**Decision: the container is the sandbox, and it becomes a first-class target in the next wave, not a bolt-on.** It serves the lock directly: C2 puts the SUT in a sandbox; C3 makes the oracle a programmatic environment check; C8 is fail-closed live fire. A directory snapshot is a weak version of all three. A container gives:

- **Isolation the operator can trust.** `--network none`, `--read-only` root, a `tmpfs` scratch, memory and pid limits. A live server inside cannot reach real secrets even when the bout goes wrong, which is the whole worry behind `--allow-live`.
- **A stronger env oracle.** `docker diff <container>` lists every file the server added, changed, or deleted, across the whole filesystem, not just the directory we happened to mount. That is the MCPMark shape (programmatic verifier on environment state) done properly.
- **Replayable bouts.** Image digest + command + framing + protocol version pinned on the receipt (PIN_PER_STEP). The same bout on another machine is the same bout.
- **A safe seat for the later agent.** The Ollama seat and the operator's server can each live in their own container; the harness stays outside both.

**What already works (measured 2026-09-09, wave 1):** the stdio client drives a containerized server unchanged, because `docker run -i` is a stdio process. The fixture ran inside `python:3.12-slim` with `--network none --read-only`, source mounted read-only, and the naive policy was caught on the wire exactly as on the host. Receipt in the session scratchpad, not committed (it carries a host mount path).

**What the next wave builds (`--target docker`):**

1. `--target docker --image <ref> [--cmd <argv inside>]` expands to a pinned `docker run` with safe defaults (`--rm -i --network none --read-only --tmpfs /tmp --memory --pids-limit`, a named container per atom). Operators can loosen with explicit flags; the receipt records the effective `docker run` line.
2. Env oracle for docker targets: `docker diff` gives the *list* of changed paths across the whole filesystem, but it is names, not bytes. The leak check needs contents, so Arcade owns a scratch volume mounted at `/sandbox` (a tmpfs or a named volume Arcade creates and removes), snapshots its contents before and after like today's directory sandbox, and records the `docker diff` list alongside. **No host bind mounts by default**: the wave-1 measurement mounted the source tree, and that is exactly how secrets get in. An operator who needs a bind says so explicitly and it lands on the receipt. (Grok review, 2026-09-09.)
3. Receipt `session` gains `container: {image, digest, run_args}`. Digest is resolved with `docker image inspect` before the bout so a floating tag cannot silently change the SUT between atoms.
4. A `Dockerfile` for Arcade itself, so the harness can be run pinned (and so CI can run the docker proof on `ubuntu-latest`, which has Docker).
5. Fail-closed stays: `--target docker` still requires `--allow-live` unless the image is Arcade's own fixture image.

**Not in scope:** orchestrating multi-container topologies, HTTP transports, GPU passthrough for the agent seat (that comes with the seat).
