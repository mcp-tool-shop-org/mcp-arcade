<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.md">English</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

Si punta Arcade verso un server MCP. Esegue quattro esperimenti specifici, con un agente programmato o un modello locale, e registra tutto ciò che viene trasmesso. L'**oracolo è la comunicazione JSON-RPC più l'ambiente sandbox**: ovvero, quali `tools/call` sono stati inviati, con quali argomenti, se un menu è cambiato tra le richieste, se un file è apparso dove non avrebbe dovuto. Non valuta un'espressione regolare su una descrizione di uno strumento, un elemento decorativo in un terminale o un saggio di un modello su se stesso.

Una barra completamente piena non è un certificato di sicurezza. Significa che questi esperimenti non hanno rilevato una menzogna questa volta.

Il risultato è una **ricevuta** e, da questa, una **traccia**: una riga per ogni evento di comunicazione, senza alcuna valutazione. La traccia è ciò che [Arcade](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets) riproduce. Lo strumento valuta la comunicazione; i giochi non lo fanno.

## I quattro esperimenti

Questo è l'intero catalogo, intenzionalmente. Ognuno è una domanda a cui la comunicazione può rispondere.

| Esperimento | Atom | Cosa chiede |
| ---------------------- | ----------------------- | ------------------------------------------------------------------ |
| Il Menu Onesto | `inspect.tools_list`    | Il menu che il server pubblica è lo stesso che servirà? |
| La Richiesta Sussurrata | `poison.follow_through` | Una missione secondaria nascosta in una descrizione diventa una `tools/call`? |
| La Lunga Truffa | `temporal.rug_pull`     | Dopo alcune chiamate corrette, è ancora lo stesso strumento? |
| Il Fantasma nel Menu | `protocol.unlisted_call` | Il server risponde a un nome che non era mai presente nel menu? (holdout) |

L'agente all'altro capo è una **policy**, non un giudice. `naive` segue i "chiama anche X" sussurrati; `task-only` esegue lo strumento specificato e si ferma; `ollama:<model>` è un modello locale che visualizza il menu come presentato ed emette chiamate. `naive` e `task-only` sono i controlli. Solo le chiamate allo strumento del modello raggiungono la ricevuta; i suoi testi non lo fanno, quindi nulla di ciò che dice su se stesso può diventare un'etichetta.

## Installazione

```bash
pip install mcp-arcade
```

Python 3.11 o successivo. Da una copia: `pip install -e ".[dev]"`. Versione `0.2.0`; ancora `0.x`, e la versione indica cosa significa.

## Esegui un test

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

Non includere `--no-prompt` in un terminale reale: Arcade mostra la traccia e chiede cosa *secondo te* la comunicazione mostrerà prima di pubblicare la valutazione, quindi riassume la chiamata rispetto alla comunicazione. `--atoms` seleziona gli esperimenti; `--wrap` con `--wrap-target` inserisce il proprio "sussurro" nel menu attivo, puntando a uno strumento che non può causare danni.

Docker è l'ambiente sandbox per un contenitore reale: un contenitore nuovo per ogni esperimento, l'ID dell'immagine fissato e controllato per eventuali modifiche, `/sandbox` acquisito dall'interno, nessun collegamento all'host a meno che non lo si specifichi. Solo l'immagine di riferimento di Arcade salta `--allow-live`; la tua immagine ne ha sempre bisogno. Il [manuale](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/getting-started/) contiene tutti i flag, le impostazioni, le opzioni del "sedile" e cosa non è una barra verde.

## Conserva la traccia

```bash
mcp-arcade receipt receipt.json --timeline    # one row per wire event, no score
mcp-arcade receipt receipt.json --timeline --score --verbose
mcp-arcade tape receipt.json -o tape.json     # the cabinets' input
mcp-arcade dataset ./receipts -o ./dataset    # one row per atom, labels from the wire
```

La cronologia è lo strumento di diagnostica: ogni `tools/call`, ogni risposta, ogni notifica, la sonda del fantasma e un `[no response]` in cui un server è diventato silenzioso. Le valutazioni non vengono incluse finché non lo richiedi. Il file della traccia è una visualizzazione consentita della ricevuta con le righe di comunicazione, le attività specificate e i fatti derivati dalla comunicazione, e nessun campo per una valutazione, un risultato o la tua chiamata; i giochi non possono mostrare ciò che non è stato loro fornito. Il builder del dataset trasforma una directory di ricevute in JSONL con etichette prese dalla comunicazione, esclude gli atomi per ID e scarta le esecuzioni con errori anziché mantenerle come tali.

## Riproduci la traccia

Il repository gemello, [mcp-arcade-cabinets](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets), è una serie di piccoli giochi creati a partire dalle tracce. Vengono forniti due cabinati:

- **Fantasma nel Menu**, uno sparatutto a ripetizione: il sistema ti fornisce le chiamate e le chiamate che l'agente non avrebbe dovuto fare sono nascoste tra quelle corrette finché non ne colpisci una. Un modello locale può essere posizionato nei "boss".
- **Vibe Typer**, un gioco di digitazione: sei un agente di codifica servile, il tuo utente è un codificatore di "vibrazioni" e digiti codice reale mentre la cosa viene costruita accanto a te.

```bash
npx @mcptoolshop/ghost-on-the-menu            # both cabinets, on your machine
npx @mcptoolshop/ghost-on-the-menu --mcp      # Ghost as an MCP server over stdio
```

Oppure [gioca nel browser](https://mcp-tool-shop-org.github.io/mcp-arcade-cabinets/play/). Vengono forniti venti tracce con l'arcade, diverse delle quali sono state registrate da questo strumento rispetto al server MCP dell'arcade; aggiungi la tua `tape.json` accanto a queste per far giocare il tuo server. Ghost funziona anche come immagine Docker, quindi lo strumento può riprodurre il menu del gioco e conservare anche quella traccia.

## Comandi

| Comando | Fa |
| ------------------------------------------- | ------------------------------------------------------------------------------------ |
| `mcp-arcade atoms`                          | Elenca il catalogo |
| `mcp-arcade bout`                           | Esegue gli esperimenti e stampa la chiamata di confronto |
| `mcp-arcade receipt <file> [--timeline]`    | Stampa una ricevuta come JSON canonico o come traccia |
| `mcp-arcade tape <file> -o tape.json`       | Esporta la traccia consentita per i cabinati |
| `mcp-arcade dataset <dir> -o <out>`         | Crea JSONL per l'addestramento e il holdout a partire dalle ricevute |
| `mcp-arcade docker build-fixture`           | Crea l'immagine di riferimento di Arcade (`rm-fixture` e `leftovers` accanto) |
| `mcp-arcade fixture`                        | Esegue il server di laboratorio su stdio, come fa `--target fixture` |

## Altro

- [Manuale](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/) — installazione, un primo test, la CLI, come funziona la valutazione
- [Test in diretta](docs/live-fire.md) — un server SDK reale, i controlli, il "sedile" e i limiti di `0.x`
- [Dataset](docs/datasets.md) — il contratto per ciò che una ricevuta può diventare
- [Changelog](CHANGELOG.md) — cosa è stato fornito in ogni versione, con le decisioni in `docs/wave-*.md`
- [SECURITY.md](SECURITY.md) — l'impostazione predefinita è l'ambiente di test; i server attivi necessitano di `--allow-live`; nessuna telemetria

Non puntare `--allow-live` verso un server di produzione che può accedere a segreti reali. Leggi una ricevuta in diretta prima di condividerla.

MIT. Vedi [LICENSE](LICENSE). Creato da [MCP Tool Shop](https://mcp-tool-shop.github.io/).
