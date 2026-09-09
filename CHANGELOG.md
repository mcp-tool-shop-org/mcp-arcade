# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-09

### Added

- GameDay CLI `mcp-arcade` with three atoms: Honest Menu, Whispered Errand, Long Con
- Stdio MCP client that records every JSON-RPC message
- Bundled fixture server (`--target fixture`)
- Scripted agents `naive` and `task-only`
- Dual-axis scores (utility, integrity) and NRP so refusing all tools cannot win
- Canonical bout receipts (`mcp-arcade.bout/v1`) as the dataset seed for a later Ollama seat
- Fail-closed `--allow-live` for non-fixture targets
- Delayed score in the TUI; contrastive house call
