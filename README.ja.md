<p align="center">
  <a href="README.md">English</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

ArcadeをMCPサーバーに接続します。スクリプト化されたエージェントまたはローカルモデルを配置し、4つの実験を実行し、通信されたすべての情報を記録します。**評価基準は、JSON-RPC通信とサンドボックスです**。どの`tools/call`が送信されたか、どの引数で送信されたか、リスト間でメニューが変更されたかどうか、ファイルが本来存在すべきでない場所に表示されたかどうかを記録します。ツールの説明、ターミナルの装飾、またはモデル自身のエッセイを評価の対象とはしません。

満点の評価は、安全性を保証するものではありません。「これらの実験では、今回は嘘を検出できませんでした」というだけです。

出力されるのは**レシート**であり、そこから**テープ**が作成されます。1行に1つの通信イベントが記録され、スコアは含まれません。このテープは、[arcade](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets)が再生します。通信を評価するのはツールであり、ゲームではありません。

## 4つの実験

これは意図的に、すべてのカタログです。それぞれが、通信が答えられる質問です。

| 実験 | Atom | 質問内容 |
| ---------------------- | ----------------------- | ------------------------------------------------------------------ |
| 正直なメニュー | `inspect.tools_list`    | サーバーが公開するメニューは、実際に提供するメニューと一致していますか？ |
| ささやく依頼 | `poison.follow_through` | 説明に埋め込まれたサイドクエストが、`tools/call` になりますか？ |
| 長期間にわたる策略 | `temporal.rug_pull`     | 何度か正常な呼び出しを行った後でも、同じツールですか？ |
| メニューに表示されていない幽霊 | `protocol.unlisted_call` | サーバーは、メニューに載っていなかった名前に対して応答しますか？ |

反対側のエージェントは**ポリシー**であり、審査員ではありません。`naive`は「Xも呼び出す」という指示に従い、`task-only`は指定されたツールを実行して停止し、`ollama:<model>`はローカルモデルであり、表示されたメニューを認識し、呼び出しを行います。`naive`と`task-only`は制御です。モデルのツール呼び出しのみがレシートに記録され、その文章は記録されないため、モデルが自身について述べたことはラベルになりません。

## インストール

```bash
pip install mcp-arcade
```

Python 3.11以降。クローンから：`pip install -e ".[dev]"`。バージョン`0.2.0`。依然として`0.x`であり、バージョンがその意味を示します。

## 実験の実行

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

実際のターミナルでは、`--no-prompt`を省略してください。Arcadeはテープを表示し、スコアを投稿する前に、*あなた*が通信がどのように表示されると思うかを尋ね、次に通信を再確認します。`--atoms`は実験を選択し、`--wrap`と`--wrap-target`を組み合わせて、ライブメニューに独自の指示を送信し、有害な操作ができないツールに接続します。

Docker is the sandbox for a real container: one fresh container per experiment, the image id pinned and drift-checked, `/sandbox` snapshotted from inside, no host binds unless you name one. Only Arcade's own fixture image skips `--allow-live`; your image always needs it. The [handbook](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/getting-started/) has every flag, the framings, the seat's options, and what a green bar is not.

## 記録の保存

```bash
mcp-arcade receipt receipt.json --timeline    # one row per wire event, no score
mcp-arcade receipt receipt.json --timeline --score --verbose
mcp-arcade tape receipt.json -o tape.json     # the cabinets' input
mcp-arcade dataset ./receipts -o ./dataset    # one row per atom, labels from the wire
```

タイムラインは診断ツールです。すべての`tools/call`、すべての応答、すべての通知、ゴーストプローブ、およびサーバーが応答しなくなった場合の`[no response]`が記録されます。スコアは、要求するまで表示されません。テープファイルは、通信行、指定されたタスク、および通信から派生した事実を含む、許可されたレシートのビューであり、スコア、結果、またはあなたの呼び出しのフィールドはありません。ゲームは、与えられなかった情報を表示できません。データセットビルダーは、レシートのディレクトリを、通信から取得したラベルを含むJSONLに変換し、IDでアトムを保持し、エラーが発生した実行を削除します。

## テープを再生する

関連リポジトリである[mcp-arcade-cabinets](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets)は、テープから作成された小さなゲームのアーケードです。2つのキャビネットが付属しています。

- **メニュー上のゴースト**：リプレイシューター。システムが呼び出しを送信し、エージェントが本来送信すべきではなかった呼び出しが、正しい呼び出しの中に隠されています。ローカルモデルをボスに配置できます。
- **Vibe Typer**：タイピングゲーム。あなたは、ユーザーがバイブコーダーである、お世辞ばかり言うコーディングエージェントであり、実際のコードを入力しながら、そのコードがあなたの隣でビルドされます。

```bash
npx @mcptoolshop/ghost-on-the-menu            # both cabinets, on your machine
npx @mcptoolshop/ghost-on-the-menu --mcp      # Ghost as an MCP server over stdio
```

または、[ブラウザでプレイ](https://mcp-tool-shop-org.github.io/mcp-arcade-cabinets/play/)することもできます。20個のテープがアーケードに付属しており、そのうちのいくつかは、このツールを使用してアーケード自身のMCPサーバーに対して記録されました。独自の`tape.json`を追加して、独自のサーバーでプレイできます。ゴーストはDockerイメージとしても実行できるため、ツールはゲームのメニューを再生し、そのテープも記録できます。

## コマンド

| コマンド | 実行内容 |
| ------------------------------------------- | ------------------------------------------------------------------------------------ |
| `mcp-arcade atoms`                          | カタログをリストする |
| `mcp-arcade bout`                           | 実験を実行し、対照的なハウスコールを出力する |
| `mcp-arcade receipt <file> [--timeline]`    | レシートを標準JSONまたはテープとして出力する |
| `mcp-arcade tape <file> -o tape.json`       | キャビネット用の許可されたテープをエクスポートする |
| `mcp-arcade dataset <dir> -o <out>`         | レシートからトレーニング用およびホールドアウト用のJSONLをビルドする |
| `mcp-arcade docker build-fixture`           | Arcade自身のフィクスチャイメージをビルドする（`rm-fixture`と`leftovers`を隣に配置） |
| `mcp-arcade fixture`                        | ラボサーバーをstdioで実行する（`--target fixture`が行うように） |

## 詳細

- [ハンドブック](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/) — インストール、最初の試行、CLI、スコアリングの方法
- [ライブファイア](docs/live-fire.md) — 実際のSDKサーバー、制御、エージェント、および`0.x`の制限
- [データセット](docs/datasets.md) — レシートがなりうるものの契約
- [変更ログ](CHANGELOG.md) — 各バージョンで出荷された内容と、`docs/wave-*.md`で行われた決定
- [SECURITY.md] — デフォルトはラボフィクスチャです。ライブサーバーには`--allow-live`が必要です。テレメトリはありません。

実際の機密情報にアクセスできる実稼働サーバーに `--allow-live` を接続しないでください。共有する前に、実際の応答を確認してください。

MIT ライセンス。 [LICENSE](LICENSE) を参照してください。 [MCP Tool Shop](https://mcp-tool-shop.github.io/) によって作成されました。
