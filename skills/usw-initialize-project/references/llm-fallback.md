# Limited LLM initialization

Use this path only after both `python3` and `python` failed the Python 3.10+
version check and the user explicitly accepted the reduced guarantees. Never
use it after `init_usw.py` started or returned an error.

## Preflight

1. Resolve the nearest Git root; otherwise use the current directory.
2. Resolve all paths relative to that root. Reject any existing symbolic link,
   special filesystem object, absolute target, `.` or `..` traversal before the
   first write.
3. Continue only when `usw.yaml` is absent or byte-for-byte equal to the
   packaged `templates/usw.yaml`. Stop on custom configuration.
4. Stop if an `openspec/` path exists. Python initialization is required for
   provider detection or compatibility behavior.
5. In a Git worktree, stop if `.usw/HANDOFF.md` or `.usw/HANDOFF.next.md` is
   tracked. If `.usw/.gitignore` exists, confirm through `git check-ignore
   --no-index` that it ignores both paths.
6. Classify every destination and parent before writing. Accept only missing
   paths, regular files at file destinations, and real directories at directory
   destinations. Preserve every existing regular file byte-for-byte.

## Materialize the default standalone workspace

Create only missing paths:

- copy packaged `templates/usw.yaml` to `usw.yaml`;
- create `.usw/`, `usw/changes`, `usw/refinements`, `usw/flows`,
  `usw/reviews`, and `usw/templates/{change,task,review}`;
- create `.usw/.gitignore` with `*` and a trailing newline;
- copy the three packaged `templates/flows/flow-scenario-*.md` files to
  `usw/flows/`;
- copy every packaged `templates/change/*.md`, `templates/task/*.md`, and
  `templates/review/*.md` file to the matching subdirectory under
  `usw/templates/`.

Render missing `.usw/HANDOFF.md` from packaged `templates/local/HANDOFF.md`.
Set `status` to `idle`, `updated_at` to the current ISO 8601 timestamp,
`fresh_stale_or_unknown` to `unknown`, `one_next_action_or_none` and
`reference_or_none` to `None.`, and every other unresolved placeholder to
`none`.

Never overwrite, merge, delete, chmod, or follow links. Do not create a custom
configuration or touch OpenSpec.

## Verify and report

Read back every created file, confirm that no template placeholders remain in
`.usw/HANDOFF.md`, and confirm both local handoff paths are ignored in a Git
worktree. Report that limited LLM fallback was used, list created and preserved
paths separately, then return without starting a flow.
