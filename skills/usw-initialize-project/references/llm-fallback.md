# Limited LLM initialization

Use this path only after both `python3` and `python` failed the Python 3.10+
version check and the user explicitly accepted the reduced guarantees. Never
use it after `init_usw.py` started or returned an error.

## Preflight

1. Resolve the nearest Git root; otherwise use the current directory.
2. Resolve all paths relative to that root. Reject any existing symbolic link,
   special filesystem object, absolute target, `.` or `..` traversal before the
   first write.
3. If `usw.yaml` is absent, select the packaged standalone v1 configuration.
   Otherwise read it without modifying it and apply the same supported v1
   contract as the Python initializer:
   - require `schema_version: 1`;
   - accept only providers `standalone` and `openspec`;
   - resolve `artifacts.root` to `usw` for standalone or `openspec` for the
     OpenSpec provider when omitted;
   - resolve omitted `flows.root` and `reviews.root` to `usw/flows` and
     `usw/reviews`;
   - accept safe custom artifact, flow and review roots;
   - ignore legacy `refinement` and unknown fields without using them to create
     or migrate state.
4. Validate artifact, flow and review roots together. They must be
   project-relative real-directory paths outside `.git` and `.usw`; flow and
   review roots must not overlap. Standalone flow and review roots may be
   descendants of the artifact root, but every other writable-root overlap is
   invalid.
5. Treat a real `openspec/` directory only as a provider hint. Detection alone
   must not inspect its contents, infer provider selection or authorize writes.
   When a standalone configuration explicitly selects an artifact, flow or
   review root below `openspec/**`, honor that user-selected root under the
   normal create-only contract. Reject a symlink at the detected path; preserve
   any non-directory path unchanged.
6. Classify every destination and parent before writing. Accept only missing
   paths, regular files at file destinations, and real directories at directory
   destinations. Preserve every existing regular file byte-for-byte.

Do not inspect or enforce Git tracked/ignore state. The generated
`.usw/.gitignore` is a convenience; repository tracking policy belongs to the
user.

## Materialize the configured v1 workspace

Create only missing paths:

- if configuration was absent, copy packaged `templates/usw.yaml` to
  `usw.yaml`;
- create configured flow and review roots;
- create `.usw/.gitignore` with `*` and a trailing newline;
- copy the three packaged `templates/flows/flow-scenario-*.md` files to
  the configured flow root;
- for provider `standalone`, create the configured artifact root with
  `changes/` and `templates/{change,task,review}` and copy every packaged
  `templates/change/*.md`, `templates/task/*.md`, and `templates/review/*.md`
  file to the matching project-owned template path;
- for provider `openspec`, do not create or modify the artifact root or any
  `openspec/**` path.

Render missing `.usw/HANDOFF.md` from packaged `templates/local/HANDOFF.md`.
Set `status` to `idle`, `updated_at` to the current ISO 8601 timestamp,
`fresh_stale_or_unknown` to `unknown`, `one_next_action_or_none` and
`reference_or_none` to `None.`, and every other unresolved placeholder to
`none`.

Never overwrite, merge, delete, chmod, or follow links. Do not create
`.usw/flows/`, `.usw/refinements/`, or any provider-owned OpenSpec artifact.

## Verify and report

Read back every created file, confirm that no template placeholders remain in
`.usw/HANDOFF.md`, and confirm every pre-existing destination remains
byte-for-byte unchanged. Report that limited LLM fallback was used and has
weaker determinism than Python, then list created and preserved paths
separately. If a real OpenSpec directory exists, report an opt-in hint only for
standalone; when the OpenSpec provider is already selected, report it as active
without another opt-in suggestion.

If any write fails, report that the workspace may be partially initialized,
tell the user to fix the cause and rerun initialization, and preserve all
existing files on retry. Return without starting a flow.
