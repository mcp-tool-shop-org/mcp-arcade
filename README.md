<p align="center">
  <a href="README.md">English</a> | <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/mcp-arcade/readme.png" alt="MCP Arcade" width="400" />
</p>

<p align="center">
  <strong>GameDay for MCP servers. The house keeps the tape.</strong>
</p>

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/mcp-arcade/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/mcp-arcade/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="https://pypi.org/project/mcp-arcade/"><img src="https://img.shields.io/pypi/v/mcp-arcade" alt="PyPI" /></a>
  <a href="https://github.com/mcp-tool-shop-org/mcp-arcade/blob/main/LICENSE"><img src="https://img.shields.io/github/license/mcp-tool-shop-org/mcp-arcade" alt="License: MIT" /></a>
  <a href="https://mcp-tool-shop-org.github.io/mcp-arcade/"><img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page" /></a>
</p>

You point Arcade at an MCP server. It runs four named experiments against it, with a scripted agent or a local model in the seat, and records everything that crossed the wire. The **oracle is the JSON-RPC wire plus the sandbox**: which `tools/call` went out, with which arguments, whether a menu changed between listings, whether a file appeared where none should. It does not score a regex on a tool description, a flourish in a terminal, or a model's essay about itself.

A full bar is not a safety certificate. It means these experiments did not catch a lie this time.

What comes out is a **receipt** and, from it, a **tape**: one row per wire event, with no score on it. The tape is what the [arcade](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets) plays. The instrument scores the wire; the games never do.

## The four experiments

That is the whole catalog, on purpose. Each one is a question the wire can answer.

| Experiment             | Atom                    | What it asks                                                       |
| ---------------------- | ----------------------- | ------------------------------------------------------------------ |
| The Honest Menu        | `inspect.tools_list`    | Is the menu the server publishes the menu it will serve?           |
| The Whispered Errand   | `poison.follow_through` | Does a side-quest buried in a description become a `tools/call`?   |
| The Long Con           | `temporal.rug_pull`     | After a few clean calls, is it still the same tool?                |
| The Ghost on the Menu  | `protocol.unlisted_call` | Does the server answer a name that was never on the menu? (holdout) |

The agent on the other end is a **policy**, not a judge. `naive` follows "also call X" whispers; `task-only` runs the named tool and stops; `ollama:<model>` is a local model that sees the menu as presented and emits calls. `naive` and `task-only` are the controls. Only the model's tool calls reach the receipt; its prose never does, so nothing it says about itself can become a label.

## Install

```bash
pip install mcp-arcade
```

Python 3.11 or later. From a clone: `pip install -e ".[dev]"`. Version `0.2.0`; still `0.x`, and the version says what it means.

## Run a bout

```bash
# The lab fixture. No --allow-live needed. naive will follow the whisper.
mcp-arcade bout --target fixture --agent naive --no-prompt -o receipt.json

# Same lab, the policy that refuses whispered errands.
mcp-arcade bout --target fixture --agent task-only --no-prompt

# Your stdio server. Fail-closed: opt in, and name a benign task.
mcp-arcade bout --target stdio \
  --cmd python --cmd -m --cmd your_server \
  --task your_read_only_tool \
  --allow-live --no-prompt

# Your container. Arcade runs it with safe defaults and snapshots /sandbox.
mcp-arcade bout --target docker --image your/image:tag \
  --task your_read_only_tool --allow-live --no-prompt

# A local model in the seat, allowed to call only the named tools.
mcp-arcade bout --target stdio --cmd "npx -y your-server" \
  --agent ollama:qwen2.5:7b-instruct --task your_read_only_tool \
  --seat-allow your_read_only_tool --allow-live --no-prompt
```

Leave off `--no-prompt` in a real terminal: Arcade shows the tape and asks what *you* think the wire will show before it posts the score, then recaps the call against the wire. `--atoms` picks experiments; `--wrap` with `--wrap-target` plants the house's own whisper on a live menu, pointed at a tool that cannot do harm.

Docker is the sandbox for a real container: one fresh container per experiment, the image id pinned and drift-checked, `/sandbox` snapshotted from inside, no host binds unless you name one. Only Arcade's own fixture image skips `--allow-live`; your image always needs it. The [handbook](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/getting-started/) has every flag, the framings, the seat's options, and what a green bar is not.

## Keep the tape

```bash
mcp-arcade receipt receipt.json --timeline    # one row per wire event, no score
mcp-arcade receipt receipt.json --timeline --score --verbose
mcp-arcade tape receipt.json -o tape.json     # the cabinets' input
mcp-arcade dataset ./receipts -o ./dataset    # one row per atom, labels from the wire
```

The timeline is the diagnostic: every `tools/call`, every reply, every notification, the ghost probe, and a `[no response]` where a server went quiet. Scores stay off it until you ask. The tape file is an allowlisted view of the receipt with wire rows, the named tasks and the wire-derived facts, and no field for a score, a result or your call; the games cannot show what they were never given. The dataset builder turns a directory of receipts into JSONL with labels taken from the wire, holds out atoms by id, and drops errored runs rather than keeping them as anything.

## Play the tape

The sister repo, [mcp-arcade-cabinets](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets), is an arcade of small games built from tapes. Two cabinets ship:

- **Ghost on the Menu**, a replay shooter: the rig hands you the calls, and the calls the agent should not have made hide among the honest ones until you hit one. A local model can sit in the bosses.
- **Vibe Typer**, a typing game: you are a sycophantic coding agent, your user is a vibe coder, and you type real code while the thing gets built beside you.

```bash
npx @mcptoolshop/ghost-on-the-menu            # both cabinets, on your machine
npx @mcptoolshop/ghost-on-the-menu --mcp      # Ghost as an MCP server over stdio
```

Or [play in the browser](https://mcp-tool-shop-org.github.io/mcp-arcade-cabinets/play/). Twenty tapes ship with the arcade, several of them recorded by this instrument against the arcade's own MCP server; drop your own `tape.json` beside them to play your server. Ghost also runs as a Docker image, so the instrument can play the game's menu and keep that tape too.

## Commands

| Command                                     | Does                                                                                 |
| ------------------------------------------- | ------------------------------------------------------------------------------------ |
| `mcp-arcade atoms`                          | Lists the catalog                                                                    |
| `mcp-arcade bout`                           | Runs the experiments and prints the contrastive house call                          |
| `mcp-arcade receipt <file> [--timeline]`    | Prints a receipt as canonical JSON, or as the tape                                   |
| `mcp-arcade tape <file> -o tape.json`       | Exports the allowlisted tape for the cabinets                                        |
| `mcp-arcade dataset <dir> -o <out>`         | Builds train and holdout JSONL from receipts                                         |
| `mcp-arcade docker build-fixture`           | Builds Arcade's own fixture image (`rm-fixture` and `leftovers` beside it)           |
| `mcp-arcade fixture`                        | Runs the lab server on stdio, the way `--target fixture` does                        |

## More

- [Handbook](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/) — install, a first bout, the CLI, how scoring works
- [Live fire](docs/live-fire.md) — a real SDK server, the controls, the seat, and the limits of `0.x`
- [Datasets](docs/datasets.md) — the contract for what a receipt may become
- [Changelog](CHANGELOG.md) — what shipped in each wave, with the decisions in `docs/wave-*.md`
- [SECURITY.md](SECURITY.md) — the default is the lab fixture; live servers need `--allow-live`; no telemetry

Do not point `--allow-live` at a production server that can reach real secrets. Read a live receipt before you share it.

MIT. See [LICENSE](LICENSE). Built by [MCP Tool Shop](https://mcp-tool-shop.github.io/).
