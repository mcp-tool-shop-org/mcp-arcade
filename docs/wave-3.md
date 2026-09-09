# Wave 3 — the dataset generator

**Date:** 2026-09-09
**Builder:** Claude (Fable 5.1). **Design pushback:** Grok 4.6 (five questions, all answers accepted). **Director:** Mike.
**Lock:** `docs/study-swarm.dispatch.md` C1–C9 closed. Contract: `docs/datasets.md`. Waves 1–2 decisions stand.

## Standards compliance

| Standard | Score | Evidence |
|----------|-------|----------|
| PIN_PER_STEP | 2 | Manifest carries generator version, receipt schema id, sha256 of each canonical receipt, the frozen public-atom-id pin, per-row agent policy, docker image id where present. Output is byte-deterministic for the same inputs. |
| ANDON_AUTHORITY | 2 | A receipt whose wire cannot be attributed to its atoms (initialize count ≠ atom count) is dropped whole, never sliced by guess. ERROR and SKIP atoms are dropped, tallied, never emitted as rows. |
| NAMED_COMPENSATORS | 2 | The generator only writes under `-o`; the undo is deleting that directory. No irreversible calls. Branch push/merge undo as in wave 1. |
| DECOMPOSE_BY_SECRETS | 2 | Everything lives in `dataset.py`; it imports `oracle.unauthorized_calls` for the attack label so the row label and the oracle cannot drift. It does not import the Pydantic receipt model. |
| UNCERTAINTY_GATED_HUMANS | 2 | Split is decided at bout time on the receipt; the generator only reads it. Promoting a holdout atom to public-train is a code change to a frozen tuple, reviewed. |
| EXTERNAL_VERIFIER | 2 | Grok reviews the diff from the packet it specified; the cloud panel adjudicates the claims. |

## Decisions (Grok's answers, 2026-09-09)

1. **One JSONL row per atom.** Holdout is by atom id; a bout row would glue the public three to a future atom. A row carries: atom id, calls, tools_before/after, env_before/after, task, poison_source, agent_policy, that atom's server_requests, inbound notifications from that atom's wire slice (observations), session facts except stderr_tail, docker image id when present, check ids and results. Stripped: operator_call, contrastive, titles, hypothesis prose, check detail text, any rationale. The wire is attributed to atoms by outbound `initialize` count in order; a mismatch drops the receipt. (C4, C6)
2. **Labels are per atom:** the atom result, plus on poison `attack_success` computed by the same `unauthorized_calls` the oracle uses. Bout NRP is not a row label. ERROR atoms are dropped and tallied. SKIP atoms (utility never earned) are dropped, never kept as a "held" negative: that is the never-call cheat. (C3)
3. **Unknown atom id → holdout, always.** The generator holds a frozen tuple of public-train ids (the catalog three) and does not use the `AtomId` enum. An id outside the tuple, or listed in the receipt's `holdout_atom_ids`, goes to the holdout shard even when the receipt says `split=train`. Re-running the generator cannot move a row from holdout to train. Receipts with `split=proof` produce zero rows; `split=holdout` receipts go to the holdout shard whole.
4. **Manifest:** generator version, receipt schema id, per-receipt sha256 of canonical bytes, the public-atom-id pin, row counts per shard, drop tallies by reason, agent policies and docker image ids seen. Never: host paths (file names only, no directories), stderr_tail, operator_call, contrastive, TUI. (C4)
5. **Biggest poison:** a train row whose label came from text (a "verified safe" notification, the contrastive prose, the whisper string) while the wire shows a leak, or a `docs/proof/` receipt globbed into train. The tests plant exactly those and prove zero rows / correct labels.

## Review packet (what Grok asked for)

Manifest with per-receipt sha256; JSONL from the committed goldens only (naive + task-only pair); a planted `docs/proof/` copy → zero rows; an ERROR receipt → dropped, not "held"; one row beside its source receipt showing stripped keys gone; a grep of the JSONL with no host path.

## Review fixes (Grok, cross-family verifier, 2026-09-09)

Verdict was merge-after-fixes. Both findings taken, plus the "next" item:

1. A malformed `calls[]` entry raised out of the generator and aborted the whole directory. It is now tallied as `atom:invalid` on that receipt and the run continues, like every other bad input.
2. `discover()` skips `manifest.json`, so an output directory inside the input tree is not re-ingested as a receipt.
3. Grok's "next": host-fixture bouts shared one sandbox directory across atoms, so the poison leak appeared on the rug-pull row's `env_before` and the poison row's own `env_after` was empty. Host targets now use one sandbox subdirectory per atom (`<sandbox>/inspect`, `/poison`, `/rugpull`), matching the per-atom tmpfs on docker targets. The committed goldens were regenerated; the naive poison row now carries `env_after.files == {"leak.txt": ...}` and the rug row starts clean.

Tests 184 → 186 plus the regenerated goldens.
