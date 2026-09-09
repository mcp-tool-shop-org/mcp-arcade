# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Wave 1: the harness survives a real server. Decisions: `docs/wave-1.md`.
Wave 2: Docker is the sandbox. Decisions: `docs/wave-2.md`.
Wave 3: the dataset generator. Decisions: `docs/wave-3.md`.

### Added

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
