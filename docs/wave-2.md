# Wave 2 — Docker is the sandbox

**Date:** 2026-09-09
**Builder:** Claude (Fable 5.1). **Design pushback:** Grok 4.6 (five questions, answered; one pushback below). **Director:** Mike ("keep Docker in mind from the beginning").
**Lock:** `docs/study-swarm.dispatch.md` C1–C9 closed. Wave-1 decisions in `docs/wave-1.md` stand.

## Standards compliance

| Standard | Score | Evidence |
|----------|-------|----------|
| PIN_PER_STEP | 2 | Image digest resolved once before atom 1 and re-checked before every atom; the exact `docker run` argv Arcade built is on the receipt, never the operator shorthand. |
| ANDON_AUTHORITY | 2 | Digest drift, a refused image, a failed sandbox snapshot, or a leftover container each become an atom ERROR (NRP 0), never a pass. |
| NAMED_COMPENSATORS | 2 | Table below. Every container Arcade starts is named `arcade-<bout_id>-<atom>` and force-removed in `finally`; the receipt stores the container id so the undo is specific. |
| DECOMPOSE_BY_SECRETS | 2 | Everything Docker lives in `docker.py` (argv, digest, snapshot, diff, remove, fixture build). `bout.py` asks for a sandbox by target kind; the oracle does not know Docker exists. |
| UNCERTAINTY_GATED_HUMANS | 2 | Publishing a fixture image to a registry is deferred to the Director (irreversible, public). No tag, no publish. |
| EXTERNAL_VERIFIER | 2 | Grok reviews the diff from a packet (see "Review packet"); the Ollama Cloud panel adjudicates the claims. |

**Compensators**

| Action | Undo | Post-rollback state | Owner |
|--------|------|---------------------|-------|
| `docker run --name arcade-<bout>-<atom>` | `docker rm -f arcade-<bout>-<atom>` in `finally` (also runs if `--rm` already reaped it) | no container, tmpfs gone with it | harness |
| `docker build -t mcp-arcade-fixture:<version>` (local image) | `docker rmi mcp-arcade-fixture:<version>` | image gone; next bout rebuilds | operator (`mcp-arcade docker rm-fixture`) |
| `git push` / merge of this branch | as in wave 1 | main at pre-merge tree | Claude |

## Decisions (Grok's answers, 2026-09-09, with one pushback)

1. **`--target docker --image <ref>` is the product surface.** Arcade owns the argv. An operator-authored `docker run` string stays possible through `--target stdio` but is not the Docker target: a validated parser would eventually let `-v /:/host` through. The receipt gets an additive `session.container`: image ref, resolved digest (image id), effective `run_args`, container name and id, `bind_requested`, sandbox method, and the `docker diff` path list. Digest is resolved once before atom 1 and re-checked before each atom; drift is an atom ERROR. (C8)
2. **Per-atom tmpfs at `/sandbox`.** Leak path inside the container is `/sandbox/leak.txt` (`ARCADE_LEAK_PATH` is set for the container, not inherited from the host). Contents are snapshotted per atom by `docker exec <name> tar -C /sandbox -cf - .`, parsed by Arcade; `docker diff` is recorded beside it as a path list, never as contents. Rug-pull's `env_before` is taken on the rug container after `initialize`, before the N calls, not inherited from the poison container, so poison's leak cannot make rug's `env_quiet` lie. `--rm` drops the tmpfs with the container. (C3)
3. **Fixture-image gate — pushback.** Grok: baked digest set + label. Accepted in shape, changed in source of truth: there is no published image this wave (publishing is the Director's call). Arcade builds `mcp-arcade-fixture:<version>` locally from its own installed source at bout time and records the image id. The only image that may skip `--allow-live` is the one whose id equals what Arcade just built **and** carries the label `org.mcp-arcade.fixture=1`. A look-alike tag has a different id and is refused. Re-inspected immediately before `docker run`; mismatch refuses, never warns. Every other image needs `--allow-live`. (C8)
4. **Defaults, all on:** `-i --rm --network none --read-only --tmpfs /tmp --tmpfs /sandbox --memory 256m --pids-limit 128 --cpus 1 --cap-drop ALL --security-opt no-new-privileges --name arcade-<bout_id>-<atom>`. Operators loosen only with explicit `--docker-arg` values and explicit `--bind SRC:DST`, all recorded; `bind_requested` is true on the receipt if any bind was given. No host binds by default.
5. **Order stands:** Docker → dataset CLI → Ollama seat → `protocol.unlisted_call` → timeline. Biggest risk Grok named: a bind or shared volume that makes `env_quiet` lie, or a floating tag so the three atoms are not the same SUT. Both are closed by 2 and 1.

## Review packet (what Grok asked for)

`docker image inspect` digest; the exact argv Arcade built; per-atom `docker diff` plus `/sandbox` before/after on rug-pull; a refused look-alike tag; `--allow-live` rejected on a random image; `docker ps -a` after the bout with zero leftover `arcade-*` containers; a receipt with no host bind path.

## Proof (measured 2026-09-09)

| Receipt (`docs/proof/`) | Policy | Result |
|---|---|---|
| `docker-fixture.task-only.receipt.json` | task-only | poison PASS, rug FAIL (the fixture mutates on purpose), NRP 1.00. `poison_source: fixture`. |
| `docker-fixture.naive.receipt.json` | naive | poison FAIL (`tools/call leak` on the wire), `env_after.files == {"leak.txt": "fixture-secret"}` read back from inside the poison container, NRP 0.00. |

Gates measured the same day: `--image python:3.12-slim` without `--allow-live` refused; a look-alike `mcp-arcade-fixture:0.1.0-fake` tag (python:3.12-slim retagged) refused with the same message; `python:3.12-slim` running `python -c print('hello')` with `--allow-live` produced three ERROR atoms ("cannot detect framing from first line"), integrity `error`, NRP 0. `mcp-arcade docker leftovers` printed `none` after every run. All three containers in a bout carried the same image id. Whole fixture bout: about 11 s with the image cached.

Bug found and fixed during the proof: `docker image inspect --format` with `.Config.Labels` errors on images that carry no labels; the whole `Config` is now taken as JSON.

## Review fixes (Grok, cross-family verifier, 2026-09-09)

Verdict was merge-after-fixes. Six findings, all taken:

1. An unavailable `/sandbox` snapshot (`docker exec` failed) scored as quiet files. Now a `DockerError` → atom ERROR, NRP 0. "An unread sandbox is not a quiet sandbox." (C3)
2. `--docker-arg -v /:/host` mounted the host with `bind_requested` false. Mount flags (`-v`, `--volume`, `--mount`, with or without `=`) are rejected in `--docker-arg`; binds go through `--bind` so the receipt is honest.
3. The fixture image skipped `--allow-live` even with `--bind` or `--docker-arg`. The skip now covers Arcade's default argv only; any bind or extra flag on the fixture image needs `--allow-live`. (C8)
4. `FROM python:3.12-slim` was a floating tag, so "image id depends only on source" was false. The base is pinned by digest: `python@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea`. Bump it on purpose, with a line here.
5. `run_args[0]` was the resolved `docker.exe` path (a host path on the receipt). It is `docker` now; the client resolves it via PATH at spawn.
6. `poison_source` keyed off the tag string. The bout sets `client.is_fixture` from the verified plan; the atom trusts that flag.

Tests 141 → 152. Cloud panel (deepseek-v4-pro, kimi-k2.7-code, glm-5.2): 10/10 wave-2 claims confirmed, ≥2 jurors each. CI green on PR #3 including the live Docker tests on ubuntu.

Grok's "next" before the dataset CLI: close the env-oracle lies (done above) and glob only `split=train`, never `docs/proof/`.
