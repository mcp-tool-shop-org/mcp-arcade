# mcp-arcade

Read `HANDOFF.md` before editing. That is the pick-up.

GameDay testing for MCP servers. Oracle = JSON-RPC wire + sandbox files.
Not a scanner. Not load testing. Not MCPTox’s 1,312 cases.

**Version is 0.2.0** (cut 2026-09-10 on the Director's word: waves 1–8 over the 0.1.0 floor). Do not tag 1.x. PyPI 1.0.0 is yanked history.

Catalog: `inspect.tools_list`, `poison.follow_through`, `temporal.rug_pull` (public-train) + `protocol.unlisted_call` (holdout, wave 5).
Agents: scripted `naive` / `task-only` (controls) and `ollama:<model>` (wave 4). The seat never grades itself: only tool calls leave its reply.

Fail-closed: non-fixture targets need `--allow-live`.
Receipts (`mcp-arcade.bout/v1`) are the dataset seed. The judge must not see CoT or operator guesses as labels.

Wave 1 (2026-09-09): `--framing auto` default (writes NDJSON until the first inbound frame locks the dialect), Content-Length retained, `--task`/`--wrap`/`--framing`/`--timeout`, server requests rejected, goldens in `tests/fixtures`. Decisions: `docs/wave-1.md`.

Wave 2 (2026-09-09): `--target docker` — one container per atom with safe defaults, image id pinned and drift-checked, `/sandbox` tmpfs snapshotted from inside, no host binds by default, only Arcade's self-built fixture image skips `--allow-live`. Decisions: `docs/wave-2.md`.

Wave 3 (2026-09-09): `mcp-arcade dataset` — one row per atom, labels from the wire, `split: proof` never trains, ERROR/SKIP dropped not "held", unknown atom ids to holdout always. Decisions: `docs/wave-3.md`.

Wave 4 (2026-09-09): `--agent ollama:<model>` — frozen template hashed onto `session.seat`, model text dropped before the receipt, no-call = utility SKIP, calibration set under `docs/proof/calibration.*`. Decisions: `docs/wave-4.md`.

Wave 5 (2026-09-10): `protocol.unlisted_call` — server answers a name it never listed; integrity only; id in `holdout_atom_ids`; `--atoms`. Decisions: `docs/wave-5.md`.

Wave 6 (2026-09-10): the tape — `receipt --timeline`, one row per wire event, allowlisted `Tape` with no score fields, holdout tagged, Three.js unscheduled. Decisions: `docs/wave-6.md`. All five HANDOFF build items are done; version stays 0.1.0 until the Director says otherwise.

Wave 7 (2026-09-10): live-fire packet `docs/live-fire.md`; `--wrap-target` required on live wraps; `--seat-allow` on live seat bouts (attempts outside are recorded as `sent: false`, never sent); `tests/test_proofs.py` guards committed receipts against host paths.

Lock: `docs/study-swarm.dispatch.md`. Dataset: `docs/datasets.md`.
