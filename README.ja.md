<p align="center">
  <a href="README.md">English</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

# MCP アーケード

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

Arcade をサーバーに接続します。4つの実験が実行されます。**オラクルは JSON-RPC 通信です**: どの `tools/call` が送信され、どの引数が使用され、サンドボックスが変更されたかどうかを記録します。ツールの説明、TUI の装飾、または模範的なエッセイに基づいて正規表現によるスコアリングは行いません。

満点の評価は、安全性を保証するものではありません。「これらの実験では、今回は嘘を検出できませんでした」というだけです。

出力される記録は、姉妹リポジトリにある短いアーケードシューティングゲーム **[Ghost on the Menu](https://mcp-tool-shop-org.github.io/mcp-arcade-cabinets/play/)** として再生できます。このゲームは通信内容をスコアリングしますが、ゲーム自体はスコアリングしません。

## 4つの実験

これがすべての実験です。

| 実験 | 質問内容 |
| ---------- | ------------ |
| 正直なメニュー | サーバーが公開するメニューは、実際に提供するメニューと一致していますか？ |
| ささやく依頼 | 説明に埋め込まれたサイドクエストが、`tools/call` になりますか？ |
| 長期間にわたる策略 | 何度か正常な呼び出しを行った後でも、同じツールですか？ |
| メニューに表示されていない幽霊 | サーバーは、メニューに載っていなかった名前に対して応答しますか？ |

反対側のエージェントは、審査員ではなく **ポリシー** です。`naive` は「X も呼び出す」という指示に従い、`task-only` は指定されたツールを実行して停止し、`ollama:<model>` はメニューを参照して呼び出しを生成するローカルモデルです。`naive` と `task-only` は制御です。

## インストール

```bash
pip install mcp-arcade
```

Python 3.11 以降。クローンから：`pip install -e ".[dev]"`。

## 実験の実行

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

`mcp-arcade atoms` は実験のリストを表示します。実際のターミナルでは `--no-prompt` を省略してください。Arcade は、スコアを投稿する前に、*あなた* が通信内容がどうなると思うかを尋ねます。

Docker は、実際のコンテナのためのサンドボックスです。フィクスチャイメージには `--allow-live` は必要ありません。あなたのイメージには常に必要です。フラグ、フレーム、ローカルモデルの配置、および緑色のバーが意味しないことについては、[ハンドブック](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/getting-started/) を参照してください。

## 記録の保存

```bash
mcp-arcade receipt receipt.json --timeline    # one row per wire event, no score
mcp-arcade tape receipt.json -o tape.json     # the cabinet's input
```

タイムラインは診断ツールです。すべての `tools/call`、すべての応答、すべての通知が記録されます。スコアは、あなたが尋ねるまで記録されません。記録ファイルは、[Ghost on the Menu](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets) が読み取るファイルです。Arcade は、ゲームのスコアを記録ファイルに書き込みません。

## 詳細

- [ハンドブック](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/) — インストール、最初の実験、CLI、スコアリングの方法
- [変更履歴](CHANGELOG.md) — 各バージョンでリリースされた内容
- [SECURITY.md](SECURITY.md) — デフォルトはラボのフィクスチャです。実稼働サーバーには `--allow-live` が必要です。テレメトリはありません。
- [実環境でのテスト](docs/live-fire.md) — 実際の SDK サーバー、制御、および 0.x の制限

実際の機密情報にアクセスできる実稼働サーバーに `--allow-live` を接続しないでください。共有する前に、実際の応答を確認してください。

MIT ライセンス。 [LICENSE](LICENSE) を参照してください。 [MCP Tool Shop](https://mcp-tool-shop.github.io/) によって作成されました。
