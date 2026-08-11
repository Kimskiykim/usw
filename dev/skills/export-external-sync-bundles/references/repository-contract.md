# Repository and package contract

## Format selection

- `repo-sync-text-v1` transfers an explicit source patch against a mapped target context.
- `repo-sync-snapshot-v1` transfers the canonical tracked tree for full mirror convergence; see [snapshot-converge.md](snapshot-converge.md).

Both use a documented Base85-encoded deterministic gzip/tar transport. Encoding is not encryption, concealment, DLP approval, or permission to transfer.

## Repository boundary

- One `.sync` file represents one source range and one target context; transfer changes, never Git history.
- No network transfer, fetch, push, PR, email, commit, or supplied-target mutation occurs in this skill.
- Use the repository's canonical exporter when it can satisfy this contract. Otherwise use the packaged runner/codec.
- Keep secrets, `.env*`, exporter state, caches, logs, generated output, unrelated dependencies/manifests, and unrelated coordination/history outside scope.

Before export, read the source equivalents of its exporter, sync rules, manifest policy, tests, and `--help`. Stop if direction, baseline meaning, dependencies, or path ownership is unclear.

## Self-contained `.sync`

Patch-mode `repo-sync-text-v1` is base85 text containing a deterministic gzip/tar payload with exactly `manifest.json` and `changes.patch`. The compact manifest includes:

- format/version/direction and source base/head;
- expected target identifier and checkpoint when known;
- selected path and change inventory;
- patch SHA-256 and per-path pre/post blob SHA-256, size, mode, and Git object id;
- embedded destination bytes for pure rename recovery, protected by the recorded hash;
- rename preimage/destination requirements;
- dependency/manifest policy;
- allowed automatic operations, required validation sequence, explicit stop conditions, and receiver receipt template.

The expected target checkpoint is sender evidence, not the receiver's actual target HEAD. `sync_workflow.py receive` captures actual target HEAD from the supplied clean checkout and compares checkpoint plus path content before any disposable apply.

The manifest and patch must stay small and secret-free. Embedding destination bytes is limited to explicitly scoped rename blobs needed to prove a target-aware candidate. Inspect the manifest and scope before handoff.

## Scope and rename rules

Incremental export requires explicit paths. For every `R... old new` entry from the full `git diff --name-status --find-renames`, include both paths or exclude both. `--find-renames` selects a representation; it does not guarantee receiver applicability. A filtered one-sided rename is a path-filter defect and is rejected by the fallback exporter.

A pure rename patch commonly contains only names and a similarity marker. It cannot reconstruct an absent preimage, and Git may accept a wrong or empty preimage. Therefore content hashes, not `git apply --check` alone, decide safety.

A target-aware replacement is permitted only when all affected changes are pure `R100`, every preimage is absent, every destination is absent, embedded destination bytes match their declared hashes, and the generated add-only candidate passes check/apply/postimage validation in a disposable clone at captured target HEAD. Never synthesize an empty file or guess destination content.

## Exporter state and human checkpoint

The end-to-end runner uses `repo_sync.py export --no-update-state`; it does not mutate source protocol state. If a repository's canonical production protocol requires a checkpoint, update it only after a `READY` receipt and through that repository's explicit procedure. The checkpoint is after the exported head and outside the bundle.

Record direction, source base/head, expected and actual target checkpoints, artifact and patch hashes, included scope/exclusions, outcome/classification, validation evidence, and `real_target_modified: false`. Do not copy historical AEF/PD/ACP checkpoint entries into this skill.
