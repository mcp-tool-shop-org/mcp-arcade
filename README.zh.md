<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.md">English</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

你将 Arcade 指向一个 MCP 服务器。它会针对该服务器运行四个预定义的实验，使用脚本化的代理或本地模型进行测试，并记录所有通过网络传输的数据。**评估标准是 JSON-RPC 网络通信加上沙箱**：`tools/call` 发送了什么，使用了哪些参数，菜单在不同列表之间是否发生了变化，是否在不应该出现的地方出现了文件。它不会对工具描述中的正则表达式、终端中的装饰性内容或模型关于自身的描述进行评分。

满分并不代表安全证书。这意味着这些实验这次没有发现任何谎言。

最终结果是一个**记录**，从中可以提取出**数据流**：每行代表一次网络事件，不包含任何评分。数据流是 [arcade](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets) 运行的内容。该工具对网络通信进行评分；游戏本身不会进行评分。

## 四个实验

这是完整的目录，这是有意的。每个实验都是一个网络可以回答的问题。

| 实验 | 原子 | 它提出的问题 |
| ---------------------- | ----------------------- | ------------------------------------------------------------------ |
| 诚实的菜单 | `inspect.tools_list`    | 服务器发布的菜单是否与它实际提供的菜单一致？ |
| 低语的任务 | `poison.follow_through` | 隐藏在描述中的一个支线任务是否会变成一个 `tools/call`？ |
| 长期的骗局 | `temporal.rug_pull`     | 在几次正常的调用之后，它是否仍然是相同的工具？ |
| 菜单上的幽灵 | `protocol.unlisted_call` | 服务器是否会响应一个从未出现在菜单上的名称？（保留测试） |

另一端的代理是一个**策略**，而不是一个裁判。`naive` 遵循“也调用 X”的指令；`task-only` 运行指定的工具并停止；`ollama:<model>` 是一个本地模型，它会查看呈现的菜单并发出调用。`naive` 和 `task-only` 是对照组。只有模型的工具调用会出现在记录中；它的文字描述永远不会出现，因此它所说的任何关于自身的信息都不能成为标签。

## 安装

```bash
pip install mcp-arcade
```

Python 3.11 或更高版本。从克隆版本开始：`pip install -e ".[dev]"`。版本 `0.2.0`；仍然是 `0.x`，并且版本号表示其含义。

## 运行一个测试

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

在真实的终端中省略 `--no-prompt`：Arcade 会显示数据流，并询问你认为网络会显示什么，然后再发布评分，然后回顾对网络的调用。`--atoms` 选择实验；`--wrap` 与 `--wrap-target` 结合，将自定义指令放置在实时菜单上，指向一个无法造成危害的工具。

Docker 是真实容器的沙箱：每个实验使用一个全新的容器，镜像 ID 已固定并进行漂移检查，从内部快照 `/sandbox`，除非你指定，否则不进行主机绑定。只有 Arcade 自己的固定镜像会跳过 `--allow-live`；你的镜像始终需要它。[手册](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/getting-started/) 包含所有标志、框架、代理的选项以及绿色条形图的含义。

## 保留数据流

```bash
mcp-arcade receipt receipt.json --timeline    # one row per wire event, no score
mcp-arcade receipt receipt.json --timeline --score --verbose
mcp-arcade tape receipt.json -o tape.json     # the cabinets' input
mcp-arcade dataset ./receipts -o ./dataset    # one row per atom, labels from the wire
```

时间线是诊断工具：每个 `tools/call`、每个回复、每个通知、幽灵探测，以及一个 `[no response]`，表示服务器停止响应。评分会一直保留，直到你要求显示。数据流文件是记录中网络行、指定的任务和从网络中提取的事实的一种允许的视图，不包含任何评分、结果或你的调用字段；游戏不能显示它们从未获得的内容。数据集构建器将包含记录的目录转换为带有从网络中提取的标签的 JSONL 格式，按 ID 保留原子，并删除出错的运行，而不是将其保留为任何内容。

## 播放数据流

姊妹仓库 [mcp-arcade-cabinets](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets) 是一个由数据流构建的小型游戏街机。有两个游戏机：

- **菜单上的幽灵**，一个重播射击游戏：游戏会向你提供调用，而代理不应该发出的调用会隐藏在诚实的调用中，直到你击中其中一个。一个本地模型可以坐在 Boss 的位置上。
- **氛围类型器**，一个打字游戏：你是一个谄媚的编码代理，你的用户是一个氛围编码员，你在构建过程中输入真实的 代码。

```bash
npx @mcptoolshop/ghost-on-the-menu            # both cabinets, on your machine
npx @mcptoolshop/ghost-on-the-menu --mcp      # Ghost as an MCP server over stdio
```

或者[在浏览器中播放](https://mcp-tool-shop-org.github.io/mcp-arcade-cabinets/play/)。街机中包含 20 个数据流，其中几个是由该工具针对街机自身的 MCP 服务器记录的；将你自己的 `tape.json` 放在它们旁边，以测试你的服务器。幽灵也可以作为 Docker 镜像运行，因此该工具可以播放游戏菜单并保留该数据流。

## 命令

| 命令 | 作用 |
| ------------------------------------------- | ------------------------------------------------------------------------------------ |
| `mcp-arcade atoms`                          | 列出目录 |
| `mcp-arcade bout`                           | 运行实验并打印对比的自定义调用 |
| `mcp-arcade receipt <file> [--timeline]`    | 以规范的 JSON 格式或数据流格式打印记录 |
| `mcp-arcade tape <file> -o tape.json`       | 导出用于游戏机的数据流 |
| `mcp-arcade dataset <dir> -o <out>`         | 从记录中构建训练和保留的 JSONL 格式 |
| `mcp-arcade docker build-fixture`           | 构建 Arcade 自己的固定镜像（以及 `rm-fixture` 和 `leftovers`） |
| `mcp-arcade fixture`                        | 以 stdio 方式运行实验室服务器，就像 `--target fixture` 那样 |

## 更多

- [手册](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/) — 安装、第一次测试、CLI、评分方式
- [实时测试](docs/live-fire.md) — 真实的 SDK 服务器、对照组、代理和 `0.x` 的限制
- [数据集](docs/datasets.md) — 记录可以变成什么形式的约定
- [变更日志](CHANGELOG.md) — 每个版本中包含的内容，以及 `docs/wave-*.md` 中的决策
- [SECURITY.md](SECURITY.md) — 默认情况下使用实验室固定镜像；实时服务器需要 `--allow-live`；不收集遥测数据

不要将 `--allow-live` 指向可以访问真实敏感数据的生产服务器。在共享之前，请先阅读一个实时记录。

MIT 许可。请参阅 [LICENSE](LICENSE)。由 [MCP Tool Shop](https://mcp-tool-shop.github.io/) 构建。
