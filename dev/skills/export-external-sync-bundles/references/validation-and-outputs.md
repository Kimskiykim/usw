# Validation and outputs

This reference covers patch mode. For canonical full tracked-tree convergence, use [snapshot-converge.md](snapshot-converge.md) and `scripts/repo_snapshot_sync.py`; do not synthesize a whole-repository patch.

## End-to-end runner

Export against a clean local checkout representing the intended receiver context. The runner resolves source refs, reviews the selected diff, captures the expected target checkpoint, builds the self-contained handoff, then checks/applies/verifies it only in a disposable clone:

```bash
python scripts/sync_workflow.py export <source-repo> \
  --base <base> --head <head> \
  --path <old-or-approved-path> --path <new-or-approved-path> \
  --target-repo <local-target-checkout> --target-id <target-id> \
  --output <bundle>.sync --report <bundle>-receipt.json
```

The receiver supplies its clean local target checkout. The runner captures actual target HEAD; it does not trust or ask the user to copy HEAD manually:

```bash
python scripts/sync_workflow.py receive <bundle>.sync \
  --target-repo <local-target-checkout> --target-id <target-id> \
  --report <bundle>-receiver-receipt.json
```

`--replacement-output <new>.sync` may be added only to request a generated pure-rename replacement. `--check-3way` requests a constrained diagnostic probe in a disposable clone; it never applies to the supplied checkout and never grants permission to apply.

## Structured outcomes

| Outcome | Typical classification | Required action |
|---|---|---|
| `READY` | `CLEAN_APPLY`, `TARGET_AWARE_REPLACEMENT` | Candidate passed disposable check/apply/postimage validation. Preserve its receipt for an explicit receiver decision. |
| `NEEDS_REBASE_OR_BASELINE` | `MISSING_PREIMAGE`, `BASELINE_MISMATCH` | Obtain the correct preimage/baseline or generate the validated target-aware candidate named by the handoff. |
| `CONFLICT_OR_PATH_MISMATCH` | `NORMAL_CONFLICT` | Correct source scope/path mapping or target context; create a new package. |
| `ALREADY_OR_PARTIALLY_APPLIED` | `ALREADY_APPLIED`, `PARTIALLY_APPLIED` | Stop; reconcile target history/content before deciding whether anything remains. |
| `UNSAFE_STOP` | dirty worktree, invalid bundle/content, target mismatch, unsupported platform | Correct the unsafe condition; do not publish or apply. |

The JSON report is the receiver receipt. It includes outcome/classification, captured target data, candidate and patch evidence, validation details, handoff/replacement data where relevant, and `real_target_modified: false`.

## Embedded handoff contract

`repo_sync.py inspect <bundle>.sync` prints the readable manifest, marking embedded content without dumping its base85 bytes. `handoff` is machine-readable and contains contract version/direction, source base/head, expected target checkpoint, scoped inventory and dependency/manifest policy, patch/blob hashes, rename preimage requirements and destination hashes, allowed automatic operations, required validation sequence, stop conditions, and a receipt template.

The package never claims that its expected target checkpoint is actual target HEAD. Receive preflight captures the latter and compares both commit context and per-path content.

## Mandatory diagnostic sequence

When a check is surprising, preserve this order so payload integrity, path semantics, and applicability remain separate evidence:

```bash
python scripts/repo_sync.py inspect <bundle>.sync \
  --patch-out <absolute-output>.patch
cd <disposable-validation-checkout>
git apply --summary < <absolute-output>.patch
git apply --check < <absolute-output>.patch
# Only when HEAD drifted from the expected target checkpoint; diagnostic only:
git apply --3way --check < <absolute-output>.patch
```

Do not treat a successful `git apply --3way --check` exit code as readiness: Git may report conflicts with a zero status. Never hand-edit the patch, use `--reject`, force, or apply with `--3way` automatically.

| Evidence | Defect class | Required action |
|---|---|---|
| Patch passes at the mapped checkpoint, path preimages match there, but receiver checkpoint/content differs | baseline drift | Stop with `NEEDS_REBASE_OR_BASELINE`; remap/rebase and repeat normal check. |
| Full source diff reports a rename while selected scope/summary contains only one side or create/delete | path-filter defect | Include both names or exclude both, then re-export; do not edit the patch. |
| Bundle/hash/source-range verification fails, or normal check fails at the exact checkpoint with complete rename paths | patch defect | Stop publication; fix the exporter/source range and regenerate. |
| Expected preimage path is absent and verified destination bytes are unavailable | missing preimage | Return the exact handoff prompt; no reconstruction is possible. |

## Pure-rename incident rule

`--find-renames` does not make a rename self-applicable. For a pure rename, a patch can contain no blob content: an absent preimage fails, while an empty placeholder or wrong preimage can pass check/apply and silently produce an empty or wrong destination. An empty placeholder is prohibited.

If verified destination bytes are embedded, the runner may recommend or generate a target-aware add candidate only under the contract in `repository-contract.md`; it validates the candidate and destination hash in a disposable clone first. Otherwise it emits the minimal exact command/prompt needed from the sender.

Case-only renames stop as `UNSUPPORTED_PLATFORM` when `core.ignorecase=true`; on a case-sensitive fixture they remain subject to normal content and disposable validation.

## Receiver apply handoff

A `READY` receipt means candidate readiness, not permission for this skill to mutate the real target. The receiver's explicit apply phase must start from the recorded actual target HEAD and clean worktree, inspect and check the same candidate again, then record apply summary, post-apply diff, postimage hashes, required tests, resulting commit, and any exclusions in the receipt. Any drift returns to receive preflight.

This skill never performs that real apply, tests that require target mutation, commit, push, or transfer.

## Legacy tools and outputs

`validate_sync_bundle.py --mode full` still validates compatible original bundles against an explicit source range and local baseline. Target-aware replacement bundles are validated by `sync_workflow.py`, because their add-only patch intentionally differs from the original source rename diff. `render_sync_docs.py` can render legacy validation Markdown; the workflow JSON receipt remains authoritative.

Stop on unknown refs/checkpoints, dirty state, secret/scope uncertainty, source/bundle mismatch, hash failure, output collision, missing content baseline, unsupported paths, disposable diff mismatch, or an unexplained outcome. Preserve failed reports; do not label them ready.
