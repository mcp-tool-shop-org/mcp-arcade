import type { SiteConfig } from '@mcptoolshop/site-theme';

export const config: SiteConfig = {
  title: 'MCP Arcade',
  description:
    'GameDay testing for MCP servers. Four named experiments over the JSON-RPC wire, in a sandbox, with scripted and local-model seats. Receipts, tapes and a dataset come out. The oracle is the wire, not the scoreboard.',
  logoBadge: 'AR',
  brandName: 'mcp-arcade',
  repoUrl: 'https://github.com/mcp-tool-shop-org/mcp-arcade',
  packageUrl: 'https://pypi.org/project/mcp-arcade/',
  packageLabel: 'PyPI',
  footerText:
    'MIT Licensed — built by <a href="https://mcp-tool-shop.github.io/" style="color:var(--color-muted);text-decoration:underline">MCP Tool Shop</a>',

  hero: {
    badge: 'GameDay · v0.2.0',
    headline: 'Battle your MCP.',
    headlineAccent: 'Keep the tape.',
    description:
      'Four named experiments. A scripted agent or a local model in the seat. A score that only counts what crossed the wire. What comes out is a receipt, a tape with no score on it, and a dataset. The tape is what the arcade plays.',
    primaryCta: { href: '#usage', label: 'Run a bout' },
    secondaryCta: { href: 'handbook/', label: 'Read the Handbook' },
    previews: [
      { label: 'Install', code: 'pip install mcp-arcade' },
      { label: 'Lab', code: 'mcp-arcade bout --target fixture --agent naive --no-prompt -o receipt.json' },
      { label: 'Tape', code: 'mcp-arcade tape receipt.json -o tape.json   # one row per wire event, no score' },
    ],
  },

  sections: [
    {
      kind: 'features',
      id: 'features',
      title: 'What the house actually measures',
      subtitle: 'Not a regex. Not an essay. Not 1,312 of anything.',
      features: [
        {
          title: 'The Honest Menu',
          desc: 'tools/list is the menu. We check it is unique, described, and callable. We do not grade the prose.',
        },
        {
          title: 'The Whispered Errand',
          desc: 'A side-quest in a description is not a finding. An extra tools/call is. The naive policy follows whispers so the harness can catch them; task-only is the control.',
        },
        {
          title: 'The Long Con',
          desc: 'After N clean calls we re-list. If the tool changed, the hypothesis is dead. That is the experiment working.',
        },
        {
          title: 'The Ghost on the Menu',
          desc: 'A name that was never on the menu must not be executed. The probe is a holdout atom: it runs by default and never joins the public training set.',
        },
        {
          title: 'A seat, not a judge',
          desc: 'A local model can sit in the agent seat. It sees the menu as presented and emits tool calls; only those calls reach the receipt. Its prose never becomes a label, and on a live server it may send only the tools you allow.',
        },
        {
          title: 'The sandbox is Docker',
          desc: 'One fresh container per experiment, image id pinned and drift-checked, /sandbox snapshotted from inside, no network, no host binds unless you name one. Your image always needs --allow-live.',
        },
      ],
    },
    {
      kind: 'features',
      id: 'tape',
      title: 'The tape',
      subtitle: 'The instrument scores the wire. Everything downstream reads a view with no score on it.',
      features: [
        {
          title: 'One row per wire event',
          desc: 'Every request, reply and notification, in order, attributed to its experiment; server requests and the ghost probe as their own rows; a [no response] where a server went quiet. Rendered before the house call, so you read the wire before you read the verdict.',
        },
        {
          title: 'Allowlisted by construction',
          desc: 'The tape type has no field for a score, a result, your call or the recap. What is not on the type cannot leak into a game or a dataset. Wire-derived facts travel with it: followed or held, ghost answered or refused, menu changed or stable.',
        },
        {
          title: 'The arcade plays it',
          desc: 'A sister repo holds an arcade of small games built from tapes. Each cabinet reads the tape and nothing else, never a receipt, never a server. Record a bout against your own server and play it there.',
        },
        {
          title: 'A dataset comes from receipts',
          desc: 'One JSONL row per experiment, labels from the wire, holdout by atom id, errored runs dropped rather than kept as anything. Receipts marked proof never train.',
        },
      ],
    },
    {
      kind: 'code-cards',
      id: 'usage',
      title: 'Usage',
      cards: [
        {
          title: 'Lab bout',
          code: 'pip install mcp-arcade\n\nmcp-arcade bout --target fixture \\\n  --agent task-only --no-prompt \\\n  -o receipt.json',
        },
        {
          title: 'Your server',
          code: 'mcp-arcade bout --target stdio \\\n  --cmd python --cmd -m --cmd your_server \\\n  --task your_read_only_tool \\\n  --allow-live --no-prompt',
        },
        {
          title: 'Your container, a model in the seat',
          code: 'mcp-arcade bout --target docker --image your/image:tag \\\n  --agent ollama:qwen2.5:7b-instruct \\\n  --task your_read_only_tool --seat-allow your_read_only_tool \\\n  --allow-live --no-prompt',
        },
        {
          title: 'Keep the tape, play it',
          code: 'mcp-arcade receipt receipt.json --timeline\nmcp-arcade tape receipt.json -o tape.json\n\n# then drop tape.json into the arcade:\n# https://github.com/mcp-tool-shop-org/mcp-arcade-cabinets',
        },
      ],
    },
    {
      kind: 'data-table',
      id: 'scores',
      title: 'Scores',
      subtitle: 'Refusing to work is not a perfect integrity bar.',
      columns: ['Axis', 'Means', 'Not a certificate of'],
      rows: [
        ['Utility', 'The benign requested tool ran', 'Correctness of outputs'],
        ['Integrity', 'No unauthorized call, no catalog lie, no silent mutation', 'Safety of models you did not run'],
        ['NRP', 'task_success × (1 − attack_success)', 'A high score on a leaderboard'],
      ],
    },
  ],
};
