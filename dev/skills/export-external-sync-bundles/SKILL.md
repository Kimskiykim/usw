---
name: export-external-sync-bundles
description: Use when exporting, receiving, or converging self-contained .sync packages between Git repositories, including scoped patch handoffs, divergent histories, rename preimages, or a canonical internal tracked-tree snapshot for an external mirror.
---

# Git Sync Bundles

## Boundary and mode

Prepare one auditable `.sync` file without network transfer, commit, push, email, or force operations.

| Need | Mode | Read |
|---|---|---|
| Scoped source change, known baseline, rename/path diagnostics | patch | [validation-and-outputs.md](references/validation-and-outputs.md) |
| Canonical INTERNAL tracked tree must converge an EXTERNAL mirror | snapshot/converge | [snapshot-converge.md](references/snapshot-converge.md) |

Read [repository-contract.md](references/repository-contract.md) for both formats.

## Patch route

Use `scripts/sync_workflow.py export|receive`. It validates only in disposable clones and returns `READY`, `NEEDS_REBASE_OR_BASELINE`, `CONFLICT_OR_PATH_MISMATCH`, `ALREADY_OR_PARTIALLY_APPLIED`, or `UNSAFE_STOP`. Never create rename placeholders, edit patches, use `--reject`, or auto-apply `--3way`.

## Snapshot route

Use the single stdlib+Git executable `scripts/repo_snapshot_sync.py`:

```bash
python scripts/repo_snapshot_sync.py export <canonical-internal> --direction internal-to-external --output <package>.sync --report export.json --acknowledge-full-snapshot
python scripts/repo_snapshot_sync.py inspect <package>.sync
python scripts/repo_snapshot_sync.py plan <package>.sync <external-mirror> --report plan.json
python scripts/repo_snapshot_sync.py apply <package>.sync <external-mirror> --confirm-converge --report apply.json
```

Base85+gzip/tar is transport encoding, not encryption or a security control. No stealth or DLP-evasion behavior is allowed; scanner passage does not mean approval. Review tracked scope and use a corporate-approved channel before any future transfer.

Snapshot export defaults to exactly canonical Git-tracked files. It includes tracked `.gitignore`, excludes all untracked/ignored local files, and never includes `.git`. Apply stages only canonical tracked paths plus deletion of target tracked paths absent from the snapshot; it preserves unrelated untracked/ignored files and never commits or pushes.

## Completion gate

Return the `.sync` and machine-readable report only after required disposable validation. This skill must not run snapshot export/apply against real AEF/PD/ACP targets unless separately and explicitly authorized.
