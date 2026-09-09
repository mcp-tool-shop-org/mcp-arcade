# mcp-arcade

GameDay testing for MCP servers. Oracle = JSON-RPC wire + sandbox files.
Not a scanner benchmark. Not load testing. Not MCPTox's 1,312 cases.

v1 catalog: `inspect.tools_list`, `poison.follow_through`, `temporal.rug_pull`.
Agents: scripted `naive` / `task-only`. No Ollama in v1.

Fail-closed: non-fixture targets need `--allow-live`.
Receipts (`mcp-arcade.bout/v1`) are the dataset seed for a later Ollama seat.
The judge must not see CoT or operator guesses as labels.
