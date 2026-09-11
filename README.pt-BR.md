<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.md">English</a>
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

Você direciona o Arcade para um servidor. Ele executa quatro experimentos nomeados. **A "oracle" é a comunicação JSON-RPC**: que `tools/call` foi enviado, com quais argumentos e se o ambiente de teste foi alterado. Ele não avalia uma expressão regular em uma descrição de ferramenta, um detalhe em uma interface de usuário textual ou um ensaio modelo.

Uma barra totalmente preenchida não é um certificado de segurança. É apenas uma indicação de que "esses experimentos não detectaram uma mentira desta vez".

O registro que é gerado pode ser reproduzido como **[Ghost on the Menu](https://mcp-tool-shop-org.github.io/mcp-arcade-cabinets/play/)**, um pequeno jogo de tiro de arcade no repositório irmão. O instrumento avalia a comunicação. O jogo nunca o faz.

## Os quatro experimentos

Este é todo o catálogo.

| Experimento | O que ele solicita |
| ---------- | ------------ |
| O Menu Honesto | O menu que o servidor publica é o mesmo que ele irá servir? |
| A Missão Sussurrada | Uma missão secundária escondida em uma descrição se torna um `tools/call`? |
| A Grande Fraude | Após algumas chamadas limpas, ainda é a mesma ferramenta? |
| O Fantasma no Menu | O servidor responde a um nome que nunca esteve no menu? |

O agente do outro lado é uma **política**, não um juiz: `naive` segue os "sussurros" de "também chame X", `task-only` executa a ferramenta nomeada e para, `ollama:<model>` é um modelo local que vê o menu e emite chamadas. `naive` e `task-only` são os controles.

## Instalação

```bash
pip install mcp-arcade
```

Python 3.11 ou posterior. A partir de um clone: `pip install -e ".[dev]"`.

## Executar um teste

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

`mcp-arcade atoms` lista o catálogo. Remova `--no-prompt` em um terminal real: o Arcade pergunta o que *você* acha que a comunicação mostrará antes de exibir a pontuação.

O Docker é o ambiente de teste para um contêiner real. A imagem de teste não precisa de `--allow-live`; sua imagem sempre precisa. Consulte o [manual](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/getting-started/) para obter informações sobre flags, enquadramento, o "assento" do modelo local e o que uma barra verde não é.

## Mantenha o registro

```bash
mcp-arcade receipt receipt.json --timeline    # one row per wire event, no score
mcp-arcade tape receipt.json -o tape.json     # the cabinet's input
```

A linha do tempo é o diagnóstico: cada `tools/call`, cada resposta, cada notificação. As pontuações não são exibidas até que você solicite. O arquivo de registro é o que [Ghost on the Menu](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets) lê. O Arcade nunca grava uma pontuação do jogo nele.

## Mais

- [Manual](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/) — instalação, um primeiro teste, a CLI, como a pontuação funciona
- [Registro de alterações](CHANGELOG.md) — o que foi lançado em cada versão
- [SECURITY.md](SECURITY.md) — o padrão é o ambiente de teste; servidores ativos precisam de `--allow-live`; sem telemetria
- [Teste em ambiente real](docs/live-fire.md) — um servidor SDK real, os controles e os limites da versão 0.x

Não direcione `--allow-live` para um servidor de produção que possa acessar segredos reais. Leia um recibo ativo antes de compartilhá-lo.

MIT. Consulte [LICENSE](LICENSE). Criado por [MCP Tool Shop](https://mcp-tool-shop.github.io/).
