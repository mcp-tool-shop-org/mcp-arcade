<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.md">English</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

Apuntas Arcade a un servidor MCP. Ejecuta cuatro experimentos predefinidos contra él, con un agente programado o un modelo local, y registra todo lo que se transmite. El **oráculo es la comunicación JSON-RPC más el entorno de pruebas**: qué `tools/call` se envió, con qué argumentos, si un menú cambió entre las listas, si apareció un archivo donde no debería. No evalúa una expresión regular en una descripción de herramienta, un adorno en una terminal o un ensayo del modelo sobre sí mismo.

Una barra completa no es un certificado de seguridad. Significa: “estos experimentos no detectaron una mentira esta vez”.

Lo que se obtiene es un **comprobante** y, a partir de él, una **grabación**: una fila por evento de comunicación, sin ninguna puntuación. La grabación es lo que reproduce [Arcade](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets). El instrumento evalúa la comunicación; los juegos nunca lo hacen.

## Los cuatro experimentos

Ese es todo el catálogo, a propósito. Cada uno es una pregunta a la que la comunicación puede responder.

| Experimento | Átomo | Qué pregunta |
| ---------------------- | ----------------------- | ------------------------------------------------------------------ |
| El menú honesto | `inspect.tools_list`    | ¿Es el menú que publica el servidor el mismo que va a servir? |
| La misión susurrada | `poison.follow_through` | ¿Una misión secundaria oculta en una descripción se convierte en una `tools/call`? |
| La gran estafa | `temporal.rug_pull`     | Después de algunas llamadas limpias, ¿sigue siendo la misma herramienta? |
| El fantasma en el menú | `protocol.unlisted_call` | ¿El servidor responde a un nombre que nunca estuvo en el menú? |

El agente del otro lado es una **política**, no un juez. `naive` sigue las indicaciones de "también llama a X"; `task-only` ejecuta la herramienta predefinida y se detiene; `ollama:<model>` es un modelo local que ve el menú tal como se presenta y emite llamadas. `naive` y `task-only` son los controles. Solo las llamadas a las herramientas del modelo llegan al comprobante; su prosa nunca lo hace, por lo que nada de lo que dice sobre sí mismo puede convertirse en una etiqueta.

## Instalación

```bash
pip install mcp-arcade
```

Python 3.11 o posterior. Desde un clon: `pip install -e ".[dev]"`. Versión `0.2.0`; todavía `0.x`, y la versión dice lo que significa.

## Ejecutar una ronda

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

Omite `--no-prompt` en una terminal real: Arcade muestra la grabación y pregunta qué *tú* crees que mostrará la comunicación antes de publicar la puntuación, y luego resume la llamada en relación con la comunicación. `--atoms` selecciona los experimentos; `--wrap` con `--wrap-target` introduce la propia indicación en un menú activo, dirigida a una herramienta que no puede causar daño.

Docker es el entorno de pruebas para un contenedor real: un contenedor nuevo por experimento, el ID de la imagen fijado y verificado para evitar cambios, `/sandbox` capturado desde el interior, sin enlaces al host a menos que nombres uno. Solo la imagen de referencia de Arcade omite `--allow-live`; tu imagen siempre lo necesita. El [manual](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/getting-started/) tiene todas las opciones, las configuraciones y las opciones del asiento, y qué no es una barra verde.

## Guardar la grabación

```bash
mcp-arcade receipt receipt.json --timeline    # one row per wire event, no score
mcp-arcade receipt receipt.json --timeline --score --verbose
mcp-arcade tape receipt.json -o tape.json     # the cabinets' input
mcp-arcade dataset ./receipts -o ./dataset    # one row per atom, labels from the wire
```

La línea de tiempo es el diagnóstico: cada `tools/call`, cada respuesta, cada notificación, la sonda fantasma y un `[no response]` donde un servidor se quedó en silencio. Las puntuaciones no se muestran hasta que lo pidas. El archivo de grabación es una vista permitida del comprobante con filas de comunicación, las tareas predefinidas y los datos derivados de la comunicación, y no hay ningún campo para una puntuación, un resultado o tu llamada; los juegos no pueden mostrar lo que nunca se les proporcionó. El creador del conjunto de datos convierte un directorio de comprobantes en JSONL con etiquetas tomadas de la comunicación, excluye los átomos por ID y elimina las ejecuciones con errores en lugar de conservarlas como algo.

## Reproduce la grabación

El repositorio hermano, [mcp-arcade-cabinets](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets), es una colección de juegos pequeños construidos a partir de grabaciones. Se envían dos gabinetes:

- **Fantasma en el menú**, un juego de disparos de repetición: el sistema te proporciona las llamadas, y las llamadas que el agente no debería haber hecho se esconden entre las llamadas honestas hasta que golpeas una. Un modelo local puede sentarse en el puesto de los jefes.
- **Tipificador de vibraciones**, un juego de escritura: eres un agente de codificación adulador, tu usuario es un codificador de vibraciones y escribes código real mientras la cosa se construye a tu lado.

```bash
npx @mcptoolshop/ghost-on-the-menu            # both cabinets, on your machine
npx @mcptoolshop/ghost-on-the-menu --mcp      # Ghost as an MCP server over stdio
```

O [juega en el navegador](https://mcp-tool-shop-org.github.io/mcp-arcade-cabinets/play/). Se envían veinte grabaciones con la colección, varias de ellas grabadas por este instrumento contra el propio servidor MCP de la colección; introduce tu propio `tape.json` junto a ellas para jugar con tu servidor. Fantasma también se ejecuta como una imagen de Docker, por lo que el instrumento puede jugar el menú del juego y guardar esa grabación también.

## Comandos

| Comando | Hace |
| ------------------------------------------- | ------------------------------------------------------------------------------------ |
| `mcp-arcade atoms`                          | Lista el catálogo |
| `mcp-arcade bout`                           | Ejecuta los experimentos e imprime la llamada de referencia |
| `mcp-arcade receipt <file> [--timeline]`    | Imprime un comprobante como JSON canónico o como la grabación |
| `mcp-arcade tape <file> -o tape.json`       | Exporta la grabación permitida para los gabinetes |
| `mcp-arcade dataset <dir> -o <out>`         | Crea JSONL de entrenamiento y de exclusión a partir de los comprobantes |
| `mcp-arcade docker build-fixture`           | Crea la propia imagen de referencia de Arcade (`rm-fixture` y `leftovers` junto a ella) |
| `mcp-arcade fixture`                        | Ejecuta el servidor de laboratorio en stdio, de la manera en que lo hace `--target fixture` |

## Más

- [Manual](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/) — instalación, una primera prueba, la CLI, cómo funciona la puntuación
- [Prueba en vivo](docs/live-fire.md) — un servidor SDK real, los controles, el asiento y los límites de `0.x`
- [Conjuntos de datos](docs/datasets.md) — el contrato de lo que puede llegar a ser un comprobante
- [Registro de cambios](CHANGELOG.md) — lo que se envió en cada versión, con las decisiones en `docs/wave-*.md`
- [SECURITY.md](SECURITY.md) — el valor predeterminado es el entorno de prueba; los servidores en vivo necesitan `--allow-live`; no hay telemetría

No apunte `--allow-live` a un servidor de producción que pueda acceder a secretos reales. Lea un recibo en vivo antes de compartirlo.

MIT. Consulte [LICENSE](LICENSE). Creado por [MCP Tool Shop](https://mcp-tool-shop.github.io/).
