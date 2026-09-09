# mcp-arcade

Read `HANDOFF.md` before editing. That is the pick-up.

GameDay testing for MCP servers. Oracle = JSON-RPC wire + sandbox files.
Not a scanner. Not load testing. Not MCPTox’s 1,312 cases.

**Version is 0.1.0.** Do not tag 1.x. PyPI 1.0.0 is yanked history.

Floor catalog: `inspect.tools_list`, `poison.follow_through`, `temporal.rug_pull`.
Agents: scripted `naive` / `task-only`. No Ollama in 0.1.0 — adding a real agent seat is build-out, and it still does not grade itself.

Fail-closed: non-fixture targets need `--allow-live`.
Receipts (`mcp-arcade.bout/v1`) are the dataset seed. The judge must not see CoT or operator guesses as labels.

Wave 1 (2026-09-09): NDJSON default, auto-detect, `--task`/`--wrap`/`--framing`/`--timeout`, server requests rejected, goldens in `tests/fixtures`. Decisions: `docs/wave-1.md`.

Lock: `docs/study-swarm.dispatch.md`. Dataset: `docs/datasets.md`.
