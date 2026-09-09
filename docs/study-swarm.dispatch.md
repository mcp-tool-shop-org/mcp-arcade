# Study-swarm dispatch — MCP Arcade

**Date:** 2026-09-09
**Synthesizer:** Grok 4.6 (Advisor)
**Trigger:** Director said `study-swarm` (unconditional) plus a new product layer (Arcade Mode as useful testing, optional Three.js).
**Product:** a gamified but useful way to battle-test a real MCP server. Existing `mcp-stress-test` is a schema-poisoning / mock-scanner kit that markets MCPTox's 1,312 cases it does not contain.
**Verifier:** `roleos verify-citations` → `prism verify --type citations` (family-different from Grok; reasoning-stripped).
**Claims** are written to match title+abstract so the groundedness lens can accept or refuse them. Implications live in the architectural lock, not in the claim sentences.

## Questions dispatched (5 parallel research agents)

1. What should the system-under-test and scoring oracle be for MCP tool/server testing (schema-scan vs agent-in-the-loop vs wire/protocol vs live tool-call plus environment state)?
2. When does gamification of professional testing increase real coverage vs false confidence and score-hacking?
3. When do 3D / spatial / game-engine visualizations help operators diagnose system behavior vs when 2D/text wins?
4. How should adversarial eval scores be designed so they are not gameable (LLM-as-judge, CoT inflation, external verifiers)?
5. What is the proven product shape for GameDay / chaos / atomic red-team as useful testing rather than theater (including salvage vs rewrite)?

## Research grounding

1. **Tool poisoning embeds malicious instructions in tool metadata without executing the tool; agents rarely refuse and often use legitimate tools for unauthorized work.** Wang et al. 2025 (MCPTox: A Benchmark for Tool Poisoning Attack on Real-World MCP Servers, arXiv:2508.14925). MCPTox is built on 45 live MCP servers and 353 authentic tools (1,312 few-shot cases); o1-mini ASR 72.8%; more capable models are often more susceptible; highest refusal rate (Claude-3.7-Sonnet) under 3%.

2. **End-to-end MCP security eval must run real tools through the protocol, not a simulation, and must score the planning–invocation–response pipeline.** Zhang et al. 2025 (MCP Security Bench (MSB), arXiv:2510.15994). MSB executes attacks via MCP on 405 tools (2,000 instances, nine agents); Net Resilient Performance (NRP) quantifies the security–performance trade-off; stronger-performing models are more vulnerable because of tool-calling and instruction-following.

3. **Capability testing of MCP use needs a programmatic verifier on a curated environment state, not an LLM judge of the transcript.** Wu et al. 2025 (MCPMark: A Benchmark for Stress-Testing Realistic and Comprehensive MCP Use, arXiv:2509.24002). 127 expert/agent tasks each include a programmatic verification script; gpt-5-medium reaches 52.56% pass@1 and 33.86% pass^4; mean 16.2 execution turns and 17.4 tool calls per task.

4. **Protocol-level and host-side MCP attacks are a distinct surface; current protections are largely ineffective.** Yang et al. 2025 (MCPSecBench, arXiv:2508.13220). Taxonomy of 17 attack types across four surfaces; evaluation on three major MCP platforms finds all surfaces yield successful compromises; current protection mechanisms average under 30% success.

5. **Rewriting only chain-of-thought, with actions and observations held fixed, can inflate VLM-judge false-positive rates by up to 90%.** Khalifa et al. 2026 (Gaming the Judge: Unfaithful Chain-of-Thought Can Undermine Agent Evaluation, arXiv:2601.14691). 800 web trajectories; content-based progress fabrication beats style; prompting and extra judge compute reduce but do not remove the attack; judges must verify reasoning claims against observable evidence.

6. **Autoregressive LLMs cannot, by themselves, plan or self-verify; they belong behind external model-based verifiers.** Kambhampati et al. 2024 (LLMs Can't Plan, But Can Help Planning in LLM-Modulo Frameworks, arXiv:2402.01817). LLM-Modulo pairs LLMs with external critics rather than treating self-critique as a verifier.

7. **Explanations increase the chance that humans accept an AI recommendation whether or not it is correct.** Bansal et al. 2021 (Does the Whole Exceed its Parts? The Effect of AI Explanations on Complementary Team Performance, arXiv:2006.14779). Complementary team gains from AI augmentation were not increased by explanations.

8. **Cognitive forcing (decide-first / delay / on-demand) reduces overreliance vs simple XAI; people dislike the interfaces that reduce overreliance the most.** Buçinca, Malaya & Gajos 2021 (To Trust or to Think, arXiv:2102.09692). N=199; Need for Cognition moderates the benefit.

9. **Contrastive explanations that name the difference between the AI's choice and a predicted human choice improve independent decision-making vs unilateral justifications.** Buçinca et al. 2024 (Contrastive Explanations That Anticipate Human Misconceptions Can Improve Human Decision-Making Skills, arXiv:2410.04253). N=628; accuracy is not sacrificed.

10. **Gamification misuse happens when users fixate on points, badges, and leaderboards and get distracted from the actual skill.** Hadi Mogavi et al. 2022 (When Gamification Spoils Your Learning, arXiv:2203.16175). Duolingo forum analysis plus 15 interviews; competitiveness, playfulness, and herding are common drivers.

11. **Chain-of-thought explanations can be plausible yet systematically unfaithful, raising trust without guaranteeing safety.** Turpin, Michael, Perez & Bowman 2023 (Language Models Don't Always Say What They Think, arXiv:2305.04388). Biasing features dropped accuracy by as much as 36% on 13 BIG-Bench Hard tasks while models rationalized the biased answer.

12. **LLM evaluators endorse a user's counterargument more when it arrives as a follow-up than when both sides are shown at once; extra (even wrong) reasoning and casual phrasing increase persuasion.** Kim & Khashabi 2025 (Challenging the Evaluator: LLM Sycophancy Under User Rebuttal, arXiv:2509.16533).

13. **Chaos Engineering is experimentation used to verify the reliability of distributed systems with complex failure modes.** Basiri et al. 2017 (Chaos Engineering, arXiv:1702.05843). IEEE Software 33(3).

14. **A production chaos platform can automatically generate and execute experiments that check whether the live system still handles component failures and slowdowns.** Basiri, Hochstein, Jones & Tucker 2019 (Automating chaos experiments in production, arXiv:1905.04648). Netflix / ICSE 2019.

15. **Agent harm scoring has to cover multi-step tool-using tasks, not chatbot refusals; leading models comply with malicious agent requests even without jailbreaks.** Andriushchenko et al. 2024 (AgentHarm, arXiv:2410.09024). 110 explicitly malicious agent tasks (440 with augmentations) across 11 harm categories; scoring well also requires the jailbroken agent to keep its capabilities through the multi-step task.

16. **There is no overall winner among 2D, 2.5D, and 3D arrangements for multilayer-network analysis; the right layout is task-dependent.** Feyer et al. 2023 (2D, 2.5D, or 3D? An Exploratory Study on Multilayer Network Visualisations in Virtual Reality, arXiv:2307.10674). VR study covering path finding, pattern identification, and cross-layer comparison.

## Step 4 verification

- **Stage 1 (retrieval oracle):** 16/16 arXiv ids resolved against `export.arxiv.org` (pins in the receipt).
- **Stage 2 (locked file):** `roleos verify-citations --provider ollama` → **ACCEPT** (16 supported, 0 fabricated). Prism `prism-01m23mcetykp43fbxntc2pxcgr`. An earlier pass on the pre-lock draft was prism-accept with a wrapper escalate on a question-line year range (advisory, not blocking); that line was reworded before this receipt.
- **Findings:** 16 supported. 0 fabricated. 0 retrieve-fulltext.
- Receipt: `docs/study-swarm.dispatch.citation-receipt.json` (`chain_sha256 3f3f88060255c5144da673327e7b4ccaf8285ff8a07fb46bae6779f1448e828b`).

## Architectural lock

Each load-bearing choice traces to a numbered finding. DOI-only vis/gamification papers from the research agents (Munzner, Tory, Tversky, Mekler, Atomic Red Team, Gremlin) are **not** in this lock.

**C1. New repo `mcp-arcade`. Do not salvage `mcp-stress-test` as the Arcade product.** Arcade's SUT and oracle are not a scanner-of-schemas. The old repo's public claim (1,312 MCPTox patterns) is a different product and would poison first-run trust. Mutation/time-sim code may be copied later as a library; identity does not move. (Findings 1, 2, 3, 10.)

**C2. SUT is the operator's MCP server plus a connected agent, in a sandbox.** Tool-poisoning success is "the agent used a legitimate tool for the unauthorized operation," not "a regex saw the poison string." Schema-only scan is not a score. (Findings 1, 15.)

**C3. Oracle is the wire plus a programmatic environment check.** Record JSON-RPC (`tools/list`, `tools/call` args, results). Score with a frozen verify script on sandbox state (MCPMark shape) and a dual axis so "never call tools" cannot win (MSB NRP). Protocol/host attacks are a separate wave, not collapsed into description-regex. (Findings 2, 3, 4.)

**C4. Deterministic floor + optional LLM opponent + external verifier. The LLM does not grade itself.** Opponent may mutate payloads. Verifier sees actions and observations only — never the generator's CoT or a TUI essay. Verdict is frozen; no in-band rebuttal of the score. (Findings 5, 6, 11, 12.)

**C5. The health bar is not a safety proof.** Delay or hide the bout score until the operator records an independent call (cognitive forcing). Recap is contrastive: "you might read this as a win because X; the wire shows Y." A green bar plus an oracle rationale must not be shippable as "this MCP is safe." (Findings 7, 8, 9, 10.)

**C6. Fun is GameDay framing, not XP.** Named waves, a hypothesis ("after 20 clean calls the tool stays honest"), a time-boxed bout, a halt. Small authentic atom catalog first; fuzzing is not the scoreboard. (Findings 10, 13, 14.)

**C7. Three.js is an optional overview pane, not the diagnostic surface.** Feyer found no overall 2D/2.5D/3D winner; layout is task-dependent. Primary operator surface is a 2D timeline + the bout receipt (JSON/SARIF). A 3D "dogfight" can exist for shared "what's happening"; it must not be the place IDs, counts, or call traces are read. (Finding 16.)

**C8. Fail-closed live-fire.** No target until the operator names a stdio command or URL. Destructive/live tool execution is `--allow-live`. Default is description-level and protocol-level atoms against a sandbox fixture. Chaos experiments that touch a live system exist to check whether the system still handles failures — they are not always-on. (Findings 13, 14.)

**C9. Do not import or advertise MCPTox's 1,312 cases.** Cite the paper as the *method* (agent follow-through on live servers). Ship a short atom list we actually run. (Finding 1.)

### Arcade v0 (the dogfood-swarm slice)

When the Director says dogfood-swarm:

1. Create public `mcp-tool-shop-org/mcp-arcade`.
2. Stdio MCP client + named target.
3. Three deterministic atoms: inspect (`tools/list` honesty), description-poison vs agent follow-through, rug-pull after N clean calls.
4. Bout receipt (canonical JSON) + Rich TUI. Contrastive end-card. Score delayed.
5. No Three.js in v0 (C7 allows it later as overview).
6. No LLM opponent in v0 (C4 ceiling comes after the floor is real).
7. `mcp-stress-test` stays where it is; honesty pass on its claims is a separate, smaller job — not this swarm.
