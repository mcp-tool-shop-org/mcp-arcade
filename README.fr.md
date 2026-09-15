<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.md">English</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

Vous dirigez Arcade vers un serveur MCP. Il exécute quatre expériences distinctes, en utilisant un agent programmé ou un modèle local, et enregistre tout ce qui a été transmis. L'**oracle est la communication JSON-RPC plus le bac à sable** : ce qui `tools/call` a été envoyé, avec quels arguments, si un menu a changé entre les affichages, si un fichier est apparu là où il ne devrait pas y en avoir. Il n’évalue pas une expression régulière sur une description d’outil, un ornement dans un terminal, ou un essai d’un modèle sur lui-même.

Une barre pleine n’est pas un certificat de sécurité. Cela signifie que ces expériences n’ont pas détecté de mensonge cette fois-ci.

Le résultat est un **relevé** et, à partir de celui-ci, une **bande** : une ligne par événement de communication, sans évaluation. La bande est ce que [Arcade](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets) utilise. L’instrument évalue la communication ; les jeux ne le font jamais.

## Les quatre expériences

C’est l’ensemble du catalogue, intentionnellement. Chacune est une question à laquelle la communication peut répondre.

| Expérience | Atom | Ce qu’elle demande |
| ---------------------- | ----------------------- | ------------------------------------------------------------------ |
| Le menu honnête | `inspect.tools_list`    | Le menu publié par le serveur est-il le même que celui qu’il sert ? |
| La quête murmurée | `poison.follow_through` | Une quête secondaire cachée dans une description devient-elle une `tools/call` ? |
| La longue supercherie | `temporal.rug_pull`     | Après quelques appels réussis, est-ce toujours le même outil ? |
| Le fantôme dans le menu | `protocol.unlisted_call` | Le serveur répond-il à un nom qui n’était pas dans le menu ? (élément de comparaison) |

L’agent à l’autre bout est une **politique**, pas un juge. `naive` suit les instructions « appeler aussi X » ; `task-only` exécute l’outil spécifié et s’arrête ; `ollama:<model>` est un modèle local qui voit le menu tel qu’il est présenté et émet des appels. `naive` et `task-only` sont les éléments de comparaison. Seuls les appels d’outils du modèle sont enregistrés dans le relevé ; ses écrits ne le sont jamais, de sorte que rien de ce qu’il dit sur lui-même ne peut devenir une étiquette.

## Installation

```bash
pip install mcp-arcade
```

Python 3.11 ou version ultérieure. À partir d’une copie : `pip install -e ".[dev]"`. Version `0.2.0` ; toujours `0.x`, et la version indique ce qu’elle signifie.

## Exécuter une série d’expériences

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

Ne pas inclure `--no-prompt` dans un terminal réel : Arcade affiche la bande et demande ce que *vous* pensez que la communication va montrer avant d’afficher l’évaluation, puis résume l’appel par rapport à la communication. `--atoms` sélectionne les expériences ; `--wrap`, avec `--wrap-target`, implante le message propre de l’environnement dans un menu actif, pointé vers un outil qui ne peut causer aucun dommage.

Docker est le bac à sable pour un conteneur réel : un conteneur frais par expérience, l’ID de l’image est fixé et vérifié pour éviter toute dérive, `/sandbox` est instantané à l’intérieur, aucune liaison à l’hôte, sauf si vous en spécifiez une. Seule l’image de référence propre d’Arcade ne passe pas `--allow-live` ; votre image en a toujours besoin. Le [manuel](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/getting-started/) contient tous les indicateurs, les configurations, les options de l’environnement et ce qu’une barre verte n’est pas.

## Conserver la bande

```bash
mcp-arcade receipt receipt.json --timeline    # one row per wire event, no score
mcp-arcade receipt receipt.json --timeline --score --verbose
mcp-arcade tape receipt.json -o tape.json     # the cabinets' input
mcp-arcade dataset ./receipts -o ./dataset    # one row per atom, labels from the wire
```

La chronologie est le diagnostic : chaque `tools/call`, chaque réponse, chaque notification, la sonde fantôme et un `[no response]` où un serveur est devenu silencieux. Les évaluations ne sont pas incluses tant que vous ne le demandez pas. Le fichier de la bande est une vue autorisée du relevé avec les lignes de communication, les tâches spécifiées et les faits dérivés de la communication, et aucun champ pour une évaluation, un résultat ou votre appel ; les jeux ne peuvent pas montrer ce qu’on ne leur a jamais donné. Le générateur de jeu de données transforme un répertoire de relevés en JSONL avec des étiquettes tirées de la communication, conserve les atomes par ID et supprime les exécutions ayant échoué au lieu de les conserver.

## Lire la bande

Le dépôt associé, [mcp-arcade-cabinets](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets), est une arcade de petits jeux créés à partir de bandes. Deux bornes d’arcade sont fournies :

- **Fantôme dans le menu**, un jeu de tir de relecture : la configuration vous donne les appels, et les appels que l’agent n’aurait pas dû faire sont cachés parmi les appels honnêtes jusqu’à ce que vous en trouviez un. Un modèle local peut être placé dans les boss.
- **Vibe Typer**, un jeu de frappe : vous êtes un agent de codage servile, votre utilisateur est un codeur de « vibe », et vous tapez du code réel pendant que la chose est construite à côté de vous.

```bash
npx @mcptoolshop/ghost-on-the-menu            # both cabinets, on your machine
npx @mcptoolshop/ghost-on-the-menu --mcp      # Ghost as an MCP server over stdio
```

Ou [jouez dans le navigateur](https://mcp-tool-shop-org.github.io/mcp-arcade-cabinets/play/). Vingt bandes sont fournies avec l’arcade, dont plusieurs ont été enregistrées par cet instrument sur le propre serveur MCP de l’arcade ; ajoutez votre propre `tape.json` à côté pour jouer avec votre serveur. Ghost fonctionne également comme une image Docker, de sorte que l’instrument peut jouer au menu du jeu et conserver également cette bande.

## Commandes

| Commande | Fait |
| ------------------------------------------- | ------------------------------------------------------------------------------------ |
| `mcp-arcade atoms`                          | Affiche le catalogue |
| `mcp-arcade bout`                           | Exécute les expériences et affiche l’appel de comparaison |
| `mcp-arcade receipt <file> [--timeline]`    | Affiche un relevé au format JSON canonique, ou au format bande |
| `mcp-arcade tape <file> -o tape.json`       | Exporte la bande autorisée pour les bornes d’arcade |
| `mcp-arcade dataset <dir> -o <out>`         | Crée des fichiers JSONL pour l’entraînement et la comparaison à partir des relevés |
| `mcp-arcade docker build-fixture`           | Crée l’image de référence propre d’Arcade (`rm-fixture` et `leftovers` à côté) |
| `mcp-arcade fixture`                        | Exécute le serveur de laboratoire sur la sortie standard, comme le fait `--target fixture` |

## Plus

- [Manuel](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/) — installation, une première série d’expériences, l’interface de ligne de commande, le fonctionnement de l’évaluation
- [Test en direct](docs/live-fire.md) — un serveur SDK réel, les éléments de comparaison, l’environnement et les limites de `0.x`
- [Jeux de données](docs/datasets.md) — le contrat pour ce qu’un relevé peut devenir
- [Journal des modifications](CHANGELOG.md) — ce qui a été fourni dans chaque version, avec les décisions prises dans `docs/wave-*.md`
- [SECURITY.md](SECURITY.md) — par défaut, il s’agit de l’environnement de test ; les serveurs en direct ont besoin de `--allow-live` ; aucune télémétrie

Ne dirigez pas `--allow-live` vers un serveur de production qui peut accéder à des secrets réels. Lisez un relevé en direct avant de le partager.

MIT. Voir [LICENSE](LICENSE). Créé par [MCP Tool Shop](https://mcp-tool-shop.github.io/).
