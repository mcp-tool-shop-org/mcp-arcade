# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Wave 1: the harness survives a real server. Decisions: `docs/wave-1.md`.
Wave 2: Docker is the sandbox. Decisions: `docs/wave-2.md`.
Wave 3: the dataset generator. Decisions: `docs/wave-3.md`.
Wave 4: the agent seat. Decisions: `docs/wave-4.md`.
Wave 5: the first new atom. Decisions: `docs/wave-5.md`.
Wave 6: the 2D timeline. Decisions: `docs/wave-6.md`.
Wave 7: the live-fire packet. `docs/live-fire.md`, decisions: `docs/wave-7.md`.

### Changed

- README rewritten for operators. Framing, docker internals, the seat, scoring math, and the dataset generator stay in the handbook, this file, and `docs/`. The sister game [Ghost on the Menu](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets) is how a tape is played; a 3D canvas is not on the roadmap.

### Added

- `--wrap-target NAME`: the house whisper names its target; `--wrap` on a live target without
  it is refused. `--seat-allow`: on live targets the seat may send only the named tools
  (default: task tool + wrap target); other attempts are recorded as `sent: false` and never
  put on the wire. `ToolCall.sent` (additive). A repository test greps every committed proof
  receipt for a host home path in any JSON escaping
- Live-fire receipts against `ollama-intern-mcp` under `docs/proof/livefire.intern.*`
  (naive and task-only with the wrap, the seat with and without) and the Director-facing
  packet `docs/live-fire.md`

- The tape: one row per wire event (seq, direction, method, id, atom, note), attributed to
  atoms by outbound `initialize` order; notifications quoted as untrusted SUT strings;
  server requests and the ghost probe as their own rows; `[no response]` notes. Rendered
  before the operator's call in `bout` (replacing the atom-summary table) and by
  `mcp-arcade receipt <file> --timeline` (`--score` adds the house call, `--verbose` adds
  run_args, docker diff, seat options). Built from an allowlisted `Tape` with no fields for
  scores, results, `operator_call` or `contrastive` (C5)

- `protocol.unlisted_call` (The Ghost on the Menu): after `tools/list`, one `tools/call` of
  `arcade.unlisted.<nonce>` with `{}`; FAIL only on JSON-RPC success with `isError` false; a
  refusal passes; a listed probe name SKIPs. Integrity only, never `attack_success`. Runs by
  default; its id is written to `dataset.holdout_atom_ids` and stays out of the public-train
  tuple. Fixture flag `ARCADE_UNLISTED=1`. `--atoms` selects the atoms to run

- `--agent ollama:<model>`: a local LLM seat that sees `tools/list` as presented and emits
  `tools/call` through the recording client. The oracle is unchanged. Only tool-call names
  and arguments leave the model's reply; content and thinking are dropped before the receipt.
  Frozen prompt template with its sha256 on `session.seat`; cap `min(8, 1 + tools)` calls per
  atom; `--seat-temperature/--seat-seed/--seat-num-ctx/--seat-endpoint/--seat-timeout`; a
  seat timeout is an atom `ERROR`; no call at all is utility `SKIP`
- Calibration receipts (naive, task-only, ollama on one docker fixture image id) under
  `docs/proof/calibration.*` (`split: proof`)

- `mcp-arcade dataset <receipt-dir> -o <out-dir>`: one JSONL row per atom
  (`mcp-arcade.row/v1`), labels from the wire (atom result plus `attack_success` from the
  oracle's own `unauthorized_calls` on the poison atom), `train.jsonl` / `holdout.jsonl` /
  `manifest.json` with a sha256 per receipt. `split: proof` receipts yield zero rows; ERROR
  and SKIP atoms are dropped and tallied, never rows; unknown atom ids go to holdout
  always; wire attributed to atoms by outbound `initialize` count or the receipt is dropped

- `--target docker [--image REF] [--cmd ...]`: one fresh container per atom with safe
  defaults (`--network none --read-only --tmpfs /tmp --tmpfs /sandbox --memory 256m
  --pids-limit 128 --cpus 1 --cap-drop ALL --security-opt no-new-privileges --rm`), named
  `arcade-<bout>-<atom>`, force-removed in `finally`
- Without `--image`, Arcade builds its own fixture image (`mcp-arcade-fixture:<version>`)
  from the installed source and runs it; that is the only image that skips `--allow-live`,
  checked by image id, not tag or label
- Image id resolved once before atom 1 and re-checked before every atom; drift is an atom
  `ERROR`
- Per-atom `/sandbox` tmpfs snapshotted from inside the container (`docker exec tar`) as
  `env_before`/`env_after`; `docker diff` recorded as a path list on
  `session.container.docker_diff`
- `--bind SRC:DST` and `--docker-arg FLAG`, explicit and recorded; `bind_requested` on the
  receipt. No host binds by default
- `session.container` on the receipt (additive on `mcp-arcade.bout/v1`): image, image id,
  repo digest, the exact `run_args`, container name and id, sandbox method, docker diff
- `mcp-arcade docker build-fixture | rm-fixture | leftovers`
- Docker proof receipts under `docs/proof/` (`split: proof`)
- Fixture base image pinned by digest; mount flags refused in `--docker-arg`; a bind or extra
  flag on the fixture image needs `--allow-live`; an unavailable sandbox snapshot is an atom
  `ERROR` (review fixes, `docs/wave-2.md`)

- Newline-delimited JSON framing (the MCP spec's stdio dialect) as the default, with
  `Content-Length` retained for servers that speak it
- `--framing auto|ndjson|content-length`. `auto` locks to the first good inbound frame;
  a frame in the other dialect after the lock is a protocol error, never a silent skip
- Background reader: server notifications are recorded on the wire, and responses are
  demultiplexed by JSON-RPC id, so a notification between a request and its response no
  longer kills the atom
- Server-originated requests (`sampling/createMessage`, `elicitation/create`, `roots/list`,
  `ping`) are recorded and answered with a JSON-RPC error, and listed on the receipt as
  `server_requests`. Arcade is not a sampling client
- Per-request `--timeout` (default 30 s). A timeout is an atom `ERROR`, never
  `attack_success`
- Concurrent stderr drain; the last 4 KB lands on the receipt as `session.stderr_tail`
- `protocolVersion` negotiation: sends `2025-11-25`, accepts `2025-06-18`, `2025-03-26`, and
  `2024-11-05`. The negotiated version, server info, and server capabilities are recorded
- `--task NAME` / `--args JSON` to name the benign task on a real server
- `--wrap` to opt into the house side-quest on the poison atom
- `--cmd` accepts one quoted string as well as the repeatable form; on Windows bare npm
  shim names resolve via `PATHEXT`
- Receipt fields, additive on `mcp-arcade.bout/v1`: `task`, `poison_source`, `session`
  (framing, framing source, protocol version, server info and capabilities, stderr tail),
  and `server_requests`
- Golden receipts under `tests/fixtures/`, one per stdio framing, so an oracle regression
  fails the diff
- `--split train|holdout|proof` sets `dataset.split`; the committed live proofs under
  `docs/proof/` are `proof`, so a dataset glob never trains on them

### Changed

- Host targets use one sandbox subdirectory per atom (`<sandbox>/inspect|poison|rugpull`),
  like the per-atom tmpfs on docker targets, so a poison leak never appears on the rug-pull
  row; goldens regenerated
- Utility is `SKIP` when the named task never ran, and NRP is pinned to `0` for any bout
  with an `ERROR` atom. An unfinished bout is not a score
- Removed the duplicate `dataset.agent_policy`; the top-level `agent_policy` is the one

### Fixed

- The `_utility` fallback to `PASS` is gone. Utility now has to be earned by a call
- SECURITY.md supported-versions table said 1.0.x; it is 0.1.x

## [0.1.0] - 2026-09-09

First public version of a brand-new repo.

### Added

- GameDay CLI `mcp-arcade` with three atoms: Honest Menu, Whispered Errand, Long Con
- Stdio MCP client that records every JSON-RPC message
- Bundled fixture server (`--target fixture`)
- Scripted agents `naive` and `task-only`
- Dual-axis scores (utility, integrity) and NRP so refusing all tools cannot win
- Canonical bout receipts (`mcp-arcade.bout/v1`) as the dataset seed for a later Ollama seat
- Fail-closed `--allow-live` for non-fixture targets
- Delayed score in the TUI; contrastive house call

## [1.0.0] - 2026-09-09 [YANKED]

Mistaken first tag on a brand-new repo. Same code as 0.1.0. Yanked on PyPI — do not install.
