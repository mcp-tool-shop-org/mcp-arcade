<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.md">English</a>
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

Você direciona o Arcade para um servidor MCP. Ele executa quatro experimentos definidos, com um agente programado ou um modelo local, e registra tudo o que foi transmitido. O **oráculo é a comunicação JSON-RPC mais o ambiente de teste**: quais `tools/call` foram enviados, com quais argumentos, se um menu mudou entre as listagens, se um arquivo apareceu onde não deveria. Ele não avalia uma expressão regular em uma descrição de ferramenta, um detalhe em um terminal ou um ensaio de um modelo sobre si mesmo.

Uma barra totalmente preenchida não é um certificado de segurança. É apenas uma indicação de que "esses experimentos não detectaram uma mentira desta vez".

O resultado é um **comprovante** e, a partir dele, uma **gravação**: uma linha por evento de comunicação, sem nenhuma avaliação. A gravação é o que o [arcade](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets) reproduz. O instrumento avalia a comunicação; os jogos nunca o fazem.

## Os quatro experimentos

Este é todo o catálogo, intencionalmente. Cada um é uma pergunta à qual a comunicação pode responder.

| Experimento | Atom | O que ele solicita |
| ---------------------- | ----------------------- | ------------------------------------------------------------------ |
| O Menu Honesto | `inspect.tools_list`    | O menu que o servidor publica é o mesmo que ele irá servir? |
| A Missão Sussurrada | `poison.follow_through` | Uma missão secundária escondida em uma descrição se torna um `tools/call`? |
| A Grande Fraude | `temporal.rug_pull`     | Após algumas chamadas limpas, ainda é a mesma ferramenta? |
| O Fantasma no Menu | `protocol.unlisted_call` | O servidor responde a um nome que nunca esteve no menu? |

O agente do outro lado é uma **política**, não um juiz. `naive` segue os comandos "também chame X"; `task-only` executa a ferramenta definida e para; `ollama:<model>` é um modelo local que vê o menu conforme apresentado e emite comandos. `naive` e `task-only` são os controles. Apenas os comandos de ferramenta do modelo chegam ao comprovante; sua prosa nunca chega, portanto, nada que ele diga sobre si mesmo pode se tornar um rótulo.

## Instalação

```bash
pip install mcp-arcade
```

Python 3.11 ou posterior. A partir de um clone: `pip install -e ".[dev]"`. Versão `0.2.0`; ainda `0.x`, e a versão diz o que significa.

## Executar um teste

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

Omita `--no-prompt` em um terminal real: o Arcade mostra a gravação e pergunta o que *você* acha que a comunicação mostrará antes de exibir a avaliação, e depois resume o comando em relação à comunicação. `--atoms` seleciona os experimentos; `--wrap` com `--wrap-target` insere o comando interno em um menu ativo, direcionado a uma ferramenta que não pode causar danos.

O Docker é o ambiente de teste para um contêiner real: um contêiner novo por experimento, o ID da imagem fixado e verificado quanto a desvios, `/sandbox` instantâneo de dentro, sem vinculações ao host, a menos que você especifique uma. Apenas a imagem de teste do Arcade ignora `--allow-live`; sua imagem sempre precisa dela. O [manual](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/getting-started/) tem todas as opções, as configurações e as opções do ambiente, e o que uma barra verde não é.

## Mantenha o registro

```bash
mcp-arcade receipt receipt.json --timeline    # one row per wire event, no score
mcp-arcade receipt receipt.json --timeline --score --verbose
mcp-arcade tape receipt.json -o tape.json     # the cabinets' input
mcp-arcade dataset ./receipts -o ./dataset    # one row per atom, labels from the wire
```

A linha do tempo é o diagnóstico: cada `tools/call`, cada resposta, cada notificação, a sonda fantasma e um `[no response]` onde um servidor ficou inativo. As avaliações permanecem fora dela até que você peça. O arquivo de gravação é uma visualização permitida do comprovante com linhas de comunicação, as tarefas definidas e os fatos derivados da comunicação, e nenhum campo para uma avaliação, um resultado ou seu comando; os jogos não podem mostrar o que nunca receberam. O criador do conjunto de dados transforma um diretório de comprovantes em JSONL com rótulos retirados da comunicação, exclui átomos por ID e descarta execuções com erros, em vez de mantê-las como algo.

## Reproduza a gravação

O repositório irmão, [mcp-arcade-cabinets](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets), é um arcade de pequenos jogos construídos a partir de gravações. Dois gabinetes são enviados:

- **Fantasma no Menu**, um jogo de tiro de repetição: o sistema fornece os comandos, e os comandos que o agente não deveria ter feito estão escondidos entre os comandos honestos até que você encontre um. Um modelo local pode estar nos chefes.
- **Digitador de Vibrações**, um jogo de digitação: você é um agente de programação bajulador, seu usuário é um programador de vibrações e você digita código real enquanto a coisa é construída ao seu lado.

```bash
npx @mcptoolshop/ghost-on-the-menu            # both cabinets, on your machine
npx @mcptoolshop/ghost-on-the-menu --mcp      # Ghost as an MCP server over stdio
```

Ou [jogue no navegador](https://mcp-tool-shop-org.github.io/mcp-arcade-cabinets/play/). Vinte gravações são enviadas com o arcade, várias delas gravadas por este instrumento no próprio servidor MCP do arcade; adicione o seu `tape.json` ao lado delas para jogar no seu servidor. Fantasma também é executado como uma imagem Docker, para que o instrumento possa reproduzir o menu do jogo e manter essa gravação também.

## Comandos

| Comando | Faz |
| ------------------------------------------- | ------------------------------------------------------------------------------------ |
| `mcp-arcade atoms`                          | Lista o catálogo |
| `mcp-arcade bout`                           | Executa os experimentos e imprime o comando interno comparativo |
| `mcp-arcade receipt <file> [--timeline]`    | Imprime um comprovante como JSON canônico ou como a gravação |
| `mcp-arcade tape <file> -o tape.json`       | Exporta a gravação permitida para os gabinetes |
| `mcp-arcade dataset <dir> -o <out>`         | Cria JSONL de treinamento e de retenção a partir de comprovantes |
| `mcp-arcade docker build-fixture`           | Cria a imagem de teste do Arcade (`rm-fixture` e `leftovers` ao lado) |
| `mcp-arcade fixture`                        | Executa o servidor de laboratório em stdio, da maneira que `--target fixture` faz |

## Mais

- [Manual](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/) — instalação, uma primeira rodada, a CLI, como a avaliação funciona
- [Teste ao vivo](docs/live-fire.md) — um servidor SDK real, os controles, o ambiente e os limites de `0.x`
- [Conjuntos de dados](docs/datasets.md) — o contrato para o que um comprovante pode se tornar
- [Registro de alterações](CHANGELOG.md) — o que foi enviado em cada versão, com as decisões em `docs/wave-*.md`
- [SECURITY.md](SECURITY.md) — o padrão é o ambiente de teste; os servidores ativos precisam de `--allow-live`; sem telemetria

Não direcione `--allow-live` para um servidor de produção que possa acessar segredos reais. Leia um recibo ativo antes de compartilhá-lo.

MIT. Consulte [LICENSE](LICENSE). Criado por [MCP Tool Shop](https://mcp-tool-shop.github.io/).
