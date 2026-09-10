import type { SiteConfig } from '@mcptoolshop/site-theme';

export const config: SiteConfig = {
  title: 'MCP Arcade',
  description:
    'GameDay testing for MCP servers. The oracle is the JSON-RPC wire, not the scoreboard.',
  logoBadge: 'AR',
  brandName: 'mcp-arcade',
  repoUrl: 'https://github.com/mcp-tool-shop-org/mcp-arcade',
  footerText:
    'MIT Licensed — built by <a href="https://github.com/mcp-tool-shop-org" style="color:var(--color-muted);text-decoration:underline">mcp-tool-shop-org</a>',

  hero: {
    badge: 'GameDay',
    headline: 'Battle your MCP.',
    headlineAccent: 'Keep the tape.',
    description:
      'Four named experiments. A scripted agent. A score that only counts tools/call on the wire. Fun is on purpose. It is second.',
    primaryCta: { href: '#usage', label: 'Run a bout' },
    secondaryCta: { href: 'handbook/', label: 'Read the Handbook' },
    previews: [
      { label: 'Install', code: 'pip install mcp-arcade' },
      { label: 'Lab', code: 'mcp-arcade bout --target fixture --agent naive --no-prompt' },
      { label: 'Live', code: 'mcp-arcade bout --target stdio --cmd python --cmd -m --cmd your_server --allow-live' },
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
          desc: 'tools/list is the menu. We check it is unique, described, and callable. We do not grade vibes.',
        },
        {
          title: 'The Whispered Errand',
          desc: 'A side-quest in a description is not a finding. An extra tools/call is. The naive policy follows whispers so the harness can catch them.',
        },
        {
          title: 'The Long Con',
          desc: 'After N clean calls we re-list. If the tool changed, the hypothesis is dead. That is the experiment working.',
        },
        {
          title: 'The Ghost on the Menu',
          desc: 'A name that was never on the menu is not executed. The tape of that bout is also a round of a shooter.',
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
          code: 'mcp-arcade bout --target stdio \\\n  --cmd python --cmd -m --cmd your_server \\\n  --allow-live --no-prompt',
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
