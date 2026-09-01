# Canonical snapshot/converge

## Security and authorization gate

This is a full tracked-repository content transport. Review ownership, classification, tracked secrets, and recipient authorization before export, then pass `--acknowledge-full-snapshot` explicitly.

Base85 plus gzip/tar is encoding/compression for textual transport, **not encryption** and not a security control. The `.sync` extension and manifest are intentionally stable and auditable. There are no hidden members, no stealth features, no content disguising, and no DLP or scanner evasion. A `.sync` file passing a scanner **does not mean approval** to transfer it. Use the corporate-approved channel and follow enterprise DLP/security policy. There is no encryption option and no automatic network or key retrieval; a future encryption envelope requires a separate explicit policy-approved design.

The clear manifest exposes paths and hashes because the package itself contains source bytes. Treat the whole file as plaintext source content.

## Canonical export

```bash
python scripts/repo_snapshot_sync.py export <canonical-internal-repo> \
  --direction internal-to-external \
  --head <commit-or-ref> \
  --output <package>.sync \
  --report <package>-export.json \
  --acknowledge-full-snapshot
```

Default inventory is exactly `git ls-tree -r` blobs at canonical head:

- every tracked regular file or symlink is included with path, mode, size, SHA-256, Git oid, and deduplicated bytes;
- the tracked .gitignore is included because it is versioned repository behavior;
- untracked and ignored `.env`, `.usw`, caches, run state, and local secrets are not read or included;
- `.git` is forbidden as a payload path;
- a tracked secret, including a tracked `.env`, is included by the exact-tracked rule—stop and correct canonical history/scope if that is unauthorized;
- gitlinks/submodules and unsafe/non-UTF-8 paths stop export.

Text files are LF-only. The exporter records the effective text
classification from the canonical tree and rejects every CR in a text blob as
`TEXT_EOL_NOT_LF`. Explicit `-text` paths are opaque binary and retain arbitrary
bytes. `text=auto`/unspecified blobs without NUL are conservatively text.

Direction has no default: export requires the immutable `--direction internal-to-external`, and inspect rejects any reverse/tampered value. The manifest records both canonical commit and canonical tree Git object IDs, plus the independent SHA-256 tracked-content inventory.

Explicit deviations use repeatable `--allow-path <file-or-directory>` and `--deny-path <file-or-directory>`. They are sorted into the manifest together with excluded tracked paths; there are no hidden default excludes.

The encoded payload is `repo-sync-snapshot-v1`: deterministic gzip/tar members `manifest.json` plus content-addressed `blobs/<sha256>`, then Base85 text. The manifest carries direction `internal-to-external`, canonical commit/tree identity, tree content hash, full file inventory, scope deviations, authorization flags, stop conditions, command templates, and receipt template.

## Receiver inspect and deterministic plan

```bash
python scripts/repo_snapshot_sync.py inspect <package>.sync
python scripts/repo_snapshot_sync.py plan <package>.sync <external-mirror> \
  --report <package>-plan.json
```

`inspect` validates transport, LF classification, member set, paths, blob
sizes/SHA-256, and tracked-tree hash before printing the manifest. UTF-8 BOM is
accepted; UTF-16 is rejected explicitly. `plan` captures actual target HEAD and
emits sorted categories:

The receiver recomputes text classification from the tracked
`.gitattributes` carried by the snapshot. A manifest `text: false` cannot turn
an otherwise textual CRLF blob into binary; explicit `-text` must be present in
the canonical tracked attributes.

| Category | Meaning |
|---|---|
| `add` | Canonical tracked path is absent from target index. |
| `replace` | Path exists but mode or content hash differs. |
| `delete` | Target tracked path is absent from canonical manifest. |
| `unchanged` | Mode and content hash match. |

Changes return `READY / CANONICAL_CHANGES_REQUIRED`; an exact match returns `ALREADY_OR_PARTIALLY_APPLIED / IN_SYNC`. Dirty tracked/index state or an untracked/ignored path collision returns `UNSAFE_STOP`. A rename appears deterministically as delete plus add; histories need not be related.

Plan clones only the local target HEAD, copies the relevant local EOL config
and `.git/info/attributes`, applies the candidate there, and verifies exact
index blobs, modes, physical LF bytes and the whole tracked worktree. A target
with `autocrlf=true`, effective `eol=crlf`, or equivalent native CRLF policy
returns `UNSAFE_STOP / LF_WORKTREE_UNSUPPORTED`. A path that cannot be
materialized byte-exactly for a non-EOL reason—a case collision on an
ignorecase filesystem, an unwritable path, filesystem name normalization—
returns `UNSAFE_STOP / WORKTREE_INCOMPATIBLE` instead, so the diagnosis names
the real cause. The supplied target is unchanged.

## Explicit converge apply

Review the plan, then make a separate authorization decision:

```bash
python scripts/repo_snapshot_sync.py apply <package>.sync <external-mirror> \
  --confirm-converge \
  --report <package>-apply.json
```

Without `--confirm-converge`, apply stops. With it, the CLI:

1. repeats integrity, clean-tracked-state, collision, and disposable validation;
2. backs up every affected worktree file in the transaction;
3. atomically writes canonical add/replace paths and removes only target tracked delete paths;
4. stages exact blobs with `hash-object --no-filters` and `update-index`, so
   `100755` and symlink blobs do not depend on checkout filters;
5. verifies final index file list, modes, content hashes, LF policy and absence
   of unstaged tracked changes;
6. automatically restores the original index/worktree on failure;
7. emits a `git restore` rollback command pinned to the captured original
   commit for a successful staged convergence.

Untracked/ignored user files are never deleted, overwritten, staged, or added. A canonical add colliding with one—including an empty directory—stops before mutation. Absolute, repository-escaping, `.git`-targeting, or non-UTF-8 symlinks stop. The CLI never copies/removes `.git`, although normal Git staging updates the index. It performs no tests outside its disposable verification, no commit, no push, no transfer, and no force operation.

The successful receipt is `READY / CONVERGED_STAGED` with original target HEAD, plan, bundle/tree hashes, disposable and final verification, rollback command/cwd, and explicit `commit_performed: false`, `push_performed: false`.

If automatic rollback fails, the receipt is `ROLLBACK_INCOMPLETE`, sets
`real_target_modified: true`, lists affected paths, and never claims that the
target was restored.

## Honest limitations

- Only Git blob modes `100644`, `100755`, and `120000` are supported; gitlinks/submodules stop.
- Symlink creation depends on receiver platform support.
- Successful apply leaves a staged diff against unchanged target HEAD; review/tests/commit remain receiver decisions.
- Scope filters intentionally produce a partial canonical manifest; target tracked paths outside it are planned for deletion.
- No network or real-target operation is needed for export, inspect, or plan.
