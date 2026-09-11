<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.md">English</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

Si punta Arcade verso un server. Esegue quattro esperimenti specifici. **L'oracolo è l'interfaccia JSON-RPC**: che `tools/call` è stato inviato, con quali argomenti e se l'ambiente di test è stato modificato. Non valuta un'espressione regolare su una descrizione dello strumento, un elemento decorativo in un'interfaccia utente testuale o un saggio di esempio.

Una barra completamente piena non è un certificato di sicurezza. Significa semplicemente che "questi esperimenti non hanno rilevato una menzogna questa volta".

La registrazione che viene generata può essere riprodotta come **[Ghost on the Menu](https://mcp-tool-shop-org.github.io/mcp-arcade-cabinets/play/)**, un breve gioco sparatutto arcade nel repository correlato. Lo strumento valuta l'interfaccia. Il gioco non lo fa mai.

## I quattro esperimenti

Questo è l'intero catalogo.

| Esperimento | Cosa richiede |
| ---------- | ------------ |
| Il menu onesto | Il menu che il server pubblica è lo stesso che servirà? |
| La richiesta sussurrata | Una missione secondaria nascosta in una descrizione diventa un `tools/call`? |
| La lunga truffa | Dopo alcune chiamate corrette, è ancora lo stesso strumento? |
| Il fantasma nel menu | Il server risponde a un nome che non era presente nel menu? |

L'agente all'altro capo è una **policy**, non un giudice: `naive` segue i comandi sussurrati "chiama anche X", `task-only` esegue lo strumento specificato e si ferma, `ollama:<model>` è un modello locale che visualizza il menu ed emette le chiamate. `naive` e `task-only` sono i controlli.

## Installazione

```bash
pip install mcp-arcade
```

Python 3.11 o successivo. Da una copia clonata: `pip install -e ".[dev]"`.

## Esegui una sessione

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

`mcp-arcade atoms` elenca il catalogo. Ometti `--no-prompt` in un terminale reale: Arcade chiede cosa *tu* pensi che l'interfaccia mostrerà prima di pubblicare il punteggio.

Docker è l'ambiente di test per un vero container. L'immagine di esempio non richiede `--allow-live`; la tua immagine lo richiede sempre. Consulta il [manuale](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/getting-started/) per le opzioni, la configurazione, la posizione del modello locale e cosa non è una barra verde.

## Conserva la registrazione

```bash
mcp-arcade receipt receipt.json --timeline    # one row per wire event, no score
mcp-arcade tape receipt.json -o tape.json     # the cabinet's input
```

La cronologia è lo strumento di diagnostica: ogni `tools/call`, ogni risposta, ogni notifica. I punteggi non vengono visualizzati fino a quando non lo richiedi. Il file di registrazione è quello che [Ghost on the Menu](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets) legge. Arcade non scrive mai un punteggio di gioco al suo interno.

## Altro

- [Manuale](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/) — installazione, una prima sessione, l'interfaccia a riga di comando, come funziona il sistema di punteggio
- [Registro delle modifiche](CHANGELOG.md) — cosa è stato rilasciato in ogni versione
- [SECURITY.md](SECURITY.md) — l'impostazione predefinita è l'ambiente di test; i server live richiedono `--allow-live`; nessuna telemetria
- [Test in ambiente reale](docs/live-fire.md) — un server SDK reale, i controlli e i limiti della versione 0.x

Non puntare `--allow-live` verso un server di produzione che può accedere a informazioni sensibili reali. Leggi una ricevuta reale prima di condividerla.

MIT. Consulta [LICENSE](LICENSE). Creato da [MCP Tool Shop](https://mcp-tool-shop.github.io/).
