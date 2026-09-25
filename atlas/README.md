# mcp-arcade: how it works

Mapped at 2026-09-25 from commit 0c17273.

## What this is

6 parts, mostly Python (40 files), TypeScript (2) and JavaScript (1). Work enters through 4 doors; CI and Release each reach 2 parts, and CI is followed because a pull request goes through it. It publishes to PyPI. People run mcp-arcade.

## What changed since the last map

This is the first map.

## What comes in

1. **CI.** On a pull request to main touching 8 paths; on a push to main touching 8 paths; or by hand. Runs src/mcp_arcade/cli.py and tests/; checks src/.
2. **Release.** When a release is published; or by hand. Runs tests/; checks src/mcp_arcade/ and src/.
3. **Deploy site to GitHub Pages.** On a push to main touching 2 paths; or by hand. Runs site/astro.config.mjs and site/src/.
4. **mcp-arcade** (a command people run). Runs src/mcp_arcade/cli.py.

## What happens through CI

1. The workflow runs src/mcp_arcade/cli.py in src and tests/ in tests; it checks src/ in src.

## Who reads the results

CI writes nothing this map can see.

## The other doors

**Release** runs tests/, checks src/mcp_arcade/ and src/, publishes to PyPI, and uploads dist/* to the release on a release event.

**Deploy site to GitHub Pages** runs site/astro.config.mjs and site/src/, and deploys the site.

**mcp-arcade** (a command people run) runs src/mcp_arcade/cli.py.

## What breaks what

- **src** is imported only from tests, by 1 part (tests), and sits on the path of 3 doors.
- **tests** is imported by no other part and sits on the path of 2 doors.

## What tends to change together

- **src/mcp_arcade/atoms/poison.py** and **src/mcp_arcade/bout.py** changed together in 5 of 8 commits, inside the src part.

1 file changed together with its own test, as expected.

Confidence is low: fewer than 30 qualifying commits in the window, and fewer than 20 source files reach 10 revisions.

Window: 180 days; a pair counts from 3 shared commits, since the window holds fewer than 30 qualifying commits.

## What no test touches

Every code part is imported by at least one test.

## Written but never read

No place this map can see is written, so none goes unread.

## Helpers that look duplicated

No two parts export a helper that looks alike.

## Generated, never hand-edited

Nothing in this repository writes to a tracked place this map can see.

## Hand-authored

People write .github/, docs/, the repository root and site/; 4 writes with paths built at run time may land here.

## Where to start

.github/workflows/ci.yml → src/mcp_arcade/cli.py → src/mcp_arcade/__init__.py → src/mcp_arcade/atoms/poison.py → src/mcp_arcade/bout.py → src/mcp_arcade/docker.py → src/mcp_arcade/models.py → src/mcp_arcade/receipt.py

Read those in order to follow one pull request end to end.

## What this map cannot see

- 4 writes and 7 reads use paths built at run time and are not named here.
- Statistics confidence is low: fewer than 30 qualifying commits in the window, and fewer than 20 source files reach 10 revisions.

Regenerate with `npx --yes @dogfood-lab/atlas map`.
