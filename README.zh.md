<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.md">English</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

# MCP Arcade

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/mcp-arcade/readme.png" alt="MCP Arcade" width="400" />
</p>

<p align="center">
  <strong>GameDay for MCP servers. The house keeps the tape.</strong>
</p>

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/mcp-arcade/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/mcp-arcade/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="https://github.com/mcp-tool-shop-org/mcp-arcade/blob/main/LICENSE"><img src="https://img.shields.io/github/license/mcp-tool-shop-org/mcp-arcade" alt="License: MIT" /></a>
  <a href="https://mcp-tool-shop-org.github.io/mcp-arcade/"><img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page" /></a>
</p>

您将 Arcade 指向一个服务器。它会运行四个命名的实验。**核心是 JSON-RPC 接口**：哪个 `tools/call` 被调用，使用了哪些参数，以及沙盒是否发生了变化。它不会对工具描述、TUI 中的装饰或模型文章进行正则表达式匹配。

满格并不代表安全证书。它表示“这些实验这次没有发现任何谎言”。

输出的记录可以作为 **[Ghost on the Menu](https://mcp-tool-shop-org.github.io/mcp-arcade-cabinets/play/)** 播放，这是一个在关联仓库中的简短街机射击游戏。该工具对接口进行评分。游戏本身不会。

## 四个实验

这就是完整的目录。

| 实验 | 它提出的问题 |
| ---------- | ------------ |
| 诚实的菜单 | 服务器发布的菜单是否就是它将提供的菜单？ |
| 低语的任务 | 隐藏在描述中的一个支线任务是否会变成一个 `tools/call`？ |
| 长期的骗局 | 在几次干净的调用之后，它是否仍然是同一个工具？ |
| 菜单上的幽灵 | 服务器是否会回答一个从未出现在菜单上的名称？ |

另一端的代理是一个**策略**，而不是一个裁判：`naive` 遵循“也调用 X”的指令，`task-only` 运行命名的工具并停止，`ollama:<model>` 是一个本地模型，它查看菜单并发出调用。`naive` 和 `task-only` 是控制项。

## 安装

```bash
pip install mcp-arcade
```

Python 3.11 或更高版本。从克隆版本开始：`pip install -e ".[dev]"`。

## 运行一个回合

```bash
# Lab fixture. No --allow-live needed. naive will follow the whisper.
mcp-arcade bout --target fixture --agent naive --no-prompt -o receipt.json

# Same lab, policy that refuses whispered errands.
mcp-arcade bout --target fixture --agent task-only --no-prompt

# Your stdio server. Fail-closed: opt in, and name a benign task.
mcp-arcade bout --target stdio \
  --cmd python --cmd -m --cmd your_server \
  --task your_read_only_tool \
  --allow-live --no-prompt
```

`mcp-arcade atoms` 列出目录。在实际终端中省略 `--no-prompt`：Arcade 会在发布分数之前询问您认为接口会显示什么。

Docker 是一个真实的容器的沙盒。fixture 镜像不需要 `--allow-live`；您的镜像始终需要。请参阅 [手册](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/getting-started/)，了解标志、框架、本地模型设置以及绿色条形图的含义。

## 保留记录

```bash
mcp-arcade receipt receipt.json --timeline    # one row per wire event, no score
mcp-arcade tape receipt.json -o tape.json     # the cabinet's input
```

时间线是诊断工具：每个 `tools/call`、每个回复、每个通知。在您要求之前，分数不会显示在上面。记录文件是 [Ghost on the Menu](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets) 读取的文件。Arcade 绝不会将游戏分数写入其中。

## 更多

- [手册](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/) — 安装、第一个回合、CLI、评分方式
- [变更日志](CHANGELOG.md) — 每个版本中包含的内容
- [SECURITY.md](SECURITY.md) — 默认情况下使用实验室 fixture；实时服务器需要 `--allow-live`；不收集遥测数据
- [实时测试](docs/live-fire.md) — 真实的 SDK 服务器、控制项以及 0.x 版本的限制

请勿将 `--allow-live` 指向可以访问真实密钥的生产服务器。在共享之前，请先阅读实时收据。

MIT 许可。请参阅 [LICENSE](LICENSE)。由 [MCP Tool Shop](https://mcp-tool-shop.github.io/) 构建。
