<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.md">English</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

Se apunta Arcade a un servidor. Ejecuta cuatro experimentos definidos. **El oráculo es la comunicación JSON-RPC**: qué `tools/call` se envió, con qué argumentos y si el entorno de pruebas cambió. No evalúa una expresión regular en una descripción de herramienta, un adorno en una interfaz de usuario de texto o un ensayo modelo.

Una barra completa no es un certificado de seguridad. Significa: “estos experimentos no detectaron una mentira esta vez”.

La grabación que se obtiene se puede reproducir como **[Ghost on the Menu](https://mcp-tool-shop-org.github.io/mcp-arcade-cabinets/play/)**, un breve juego de disparos de arcade en el repositorio hermano. El instrumento evalúa la comunicación. El juego nunca lo hace.

## Los cuatro experimentos

Este es todo el catálogo.

| Experimento | Qué pregunta |
| ---------- | ------------ |
| El menú honesto | ¿Es el menú que publica el servidor el mismo que va a servir? |
| La misión susurrada | ¿Una misión secundaria oculta en una descripción se convierte en una `tools/call`? |
| La gran estafa | Después de algunas llamadas limpias, ¿sigue siendo la misma herramienta? |
| El fantasma en el menú | ¿El servidor responde a un nombre que nunca estuvo en el menú? |

El agente del otro lado es una **política**, no un juez: `naive` sigue los susurros de “también llama a X”, `task-only` ejecuta la herramienta definida y se detiene, `ollama:<model>` es un modelo local que ve el menú y emite llamadas. `naive` y `task-only` son los controles.

## Instalación

```bash
pip install mcp-arcade
```

Python 3.11 o posterior. Desde una copia: `pip install -e ".[dev]"`.

## Ejecutar una ronda

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

`mcp-arcade atoms` muestra el catálogo. Omita `--no-prompt` en una terminal real: Arcade pregunta qué *usted* cree que mostrará la comunicación antes de publicar la puntuación.

Docker es el entorno de pruebas para un contenedor real. La imagen de prueba no necesita `--allow-live`; su imagen siempre lo necesita. Consulte el [manual](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/getting-started/) para obtener información sobre las opciones, el formato, el modelo local y qué no es una barra verde.

## Guardar la grabación

```bash
mcp-arcade receipt receipt.json --timeline    # one row per wire event, no score
mcp-arcade tape receipt.json -o tape.json     # the cabinet's input
```

La línea de tiempo es el diagnóstico: cada `tools/call`, cada respuesta, cada notificación. Las puntuaciones no se muestran hasta que se solicite. El archivo de grabación es lo que lee [Ghost on the Menu](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets). Arcade nunca escribe una puntuación del juego en él.

## Más

- [Manual](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/) — instalación, una primera ronda, la CLI, cómo funciona la puntuación
- [Registro de cambios](CHANGELOG.md) — qué se incluyó en cada versión
- [SECURITY.md](SECURITY.md) — el valor predeterminado es el entorno de pruebas; los servidores en vivo necesitan `--allow-live`; no hay telemetría
- [Prueba en vivo](docs/live-fire.md) — un servidor SDK real, los controles y los límites de 0.x

No apunte `--allow-live` a un servidor de producción que pueda acceder a secretos reales. Lea un recibo en vivo antes de compartirlo.

MIT. Consulte [LICENSE](LICENSE). Creado por [MCP Tool Shop](https://mcp-tool-shop.github.io/).
