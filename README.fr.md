<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.md">English</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

Vous pointez Arcade vers un serveur. Il exécute quatre expériences distinctes. **L’oracle est l’interface JSON-RPC** : il enregistre quelles `tools/call` ont été envoyées, avec quels arguments, et si l’environnement de test a été modifié. Il n’évalue pas une expression régulière sur une description d’outil, un élément décoratif dans une interface utilisateur en mode texte, ou un essai type.

Une barre entièrement remplie n’est pas un certificat de sécurité. Cela signifie simplement que « ces expériences n’ont pas détecté de mensonge cette fois-ci ».

Le résultat obtenu peut être utilisé comme **[Ghost on the Menu](https://mcp-tool-shop-org.github.io/mcp-arcade-cabinets/play/)**, un court jeu d’arcade du type « shoot ‘em up » dans le dépôt associé. L’instrument évalue l’interface. Le jeu ne le fait jamais.

## Les quatre expériences

Voici le catalogue complet.

| Expérience | Ce qu’elle demande |
| ---------- | ------------ |
| Le menu honnête | Le menu publié par le serveur est-il bien le menu qu’il va servir ? |
| La mission chuchotée | Une quête secondaire cachée dans une description devient-elle une `tools/call` ? |
| La longue supercherie | Après quelques appels réussis, est-ce toujours le même outil ? |
| Le fantôme dans le menu | Le serveur répond-il à un nom qui n’était pas dans le menu ? |

L’agent à l’autre bout est une **politique**, et non un juge : `naive` suit les instructions « appeler également X », `task-only` exécute l’outil spécifié et s’arrête, `ollama:<model>` est un modèle local qui consulte le menu et génère des appels. `naive` et `task-only` sont les commandes.

## Installation

```bash
pip install mcp-arcade
```

Python 3.11 ou version ultérieure. À partir d’une copie : `pip install -e ".[dev]"`.

## Exécuter une session

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

`mcp-arcade atoms` affiche le catalogue. Supprimez `--no-prompt` dans un terminal réel : Arcade vous demande ce que *vous* pensez que l’interface va afficher avant d’afficher le score.

Docker est l’environnement de test pour un conteneur réel. L’image de référence n’a pas besoin de `--allow-live` ; votre image en a toujours besoin. Consultez le [manuel](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/getting-started/) pour connaître les options, la configuration, le modèle local et ce qu’une barre verte ne représente pas.

## Conserver l’enregistrement

```bash
mcp-arcade receipt receipt.json --timeline    # one row per wire event, no score
mcp-arcade tape receipt.json -o tape.json     # the cabinet's input
```

La chronologie est le diagnostic : chaque `tools/call`, chaque réponse, chaque notification. Les scores ne sont pas enregistrés tant que vous ne le demandez pas. Le fichier d’enregistrement est celui que [Ghost on the Menu](https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets) lit. Arcade n’y enregistre jamais le score d’un jeu.

## Plus d’informations

- [Manuel](https://mcp-tool-shop-org.github.io/mcp-arcade/handbook/) — installation, première session, l’interface en ligne de commande, le fonctionnement de l’évaluation
- [Journal des modifications](CHANGELOG.md) — ce qui a été inclus dans chaque version
- [SECURITY.md](SECURITY.md) — par défaut, il s’agit de l’environnement de test ; les serveurs en production ont besoin de `--allow-live` ; aucune télémétrie
- [Test en conditions réelles](docs/live-fire.md) — un serveur SDK réel, les commandes et les limites de la version 0.x

Ne pointez pas `--allow-live` vers un serveur de production qui peut accéder à des informations sensibles réelles. Consultez un reçu en direct avant de le partager.

MIT. Voir [LICENSE](LICENSE). Créé par [MCP Tool Shop](https://mcp-tool-shop.github.io/).
