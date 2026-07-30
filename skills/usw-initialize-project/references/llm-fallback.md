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
   - reject the removed `artifacts.provider` field;
   - resolve omitted `artifacts.root` to `usw`;
   - resolve omitted `flows.root` and `reviews.root` to `usw/flows` and
     `usw/reviews`;
   - accept optional top-level `handoff` only as unquoted boolean `true` or
     `false`, with an omitted field meaning `true`;
   - accept safe custom artifact, flow and review roots;
   - ignore legacy `refinement` and unknown fields without using them to create
     or migrate state.
4. Validate artifact, flow and review roots together. They must be
   project-relative real-directory paths outside `.git` and `.usw`; flow and
   review roots must not overlap. Flow and review roots may be
   descendants of the artifact root, but every other writable-root overlap is
   invalid.
5. Classify every destination and parent before writing. Accept only missing
   paths, regular files at file destinations, and real directories at directory
   destinations. Preserve every existing regular file byte-for-byte.

Do not inspect or enforce Git tracked/ignore state. The generated
`.usw/.gitignore` is a convenience; repository tracking policy belongs to the
user.

## Materialize the configured v1 workspace

Create only missing paths:

- if configuration was absent, copy packaged `templates/usw.yaml` to
  `usw.yaml`;
- create the configured flow root;
- create `.usw/.gitignore` with `*` and a trailing newline;
- create `<flows.root>/examples/` and copy exactly the two packaged examples
  `chat-review.md` and `dev-test.md` there.

Do not create `<artifacts.root>/changes/`, `<artifacts.root>/templates/`, or
`<reviews.root>/`. Their exact destination is created by the capability that
first needs it.

When effective `handoff` is `true`, render missing `.usw/HANDOFF.md` from
packaged `templates/local/HANDOFF.md` and replace only `{{updated_at}}` with the
current timezone-aware ISO 8601 timestamp. When `handoff` is `false`, do not
read, validate, create or modify `.usw/HANDOFF.md`.

Never overwrite, merge, delete, chmod, or follow links. Do not create
`.usw/flows/` or `.usw/refinements/`. Do not create, migrate, or remove legacy
`flow-scenario-*.md` files. Every installed example is non-normative and must
remain nested under `examples/` so the runner cannot select it directly by a
flat flow name.

## Verify and report

Read back every created file. When handoff is enabled, confirm that no template
placeholders remain in `.usw/HANDOFF.md`; when disabled, confirm only from the
write inventory that the path was not touched. Confirm every pre-existing
destination remains byte-for-byte unchanged. Report that limited LLM fallback
was used and has weaker determinism than Python, then list created and
preserved paths separately.

If any write fails, report that the workspace may be partially initialized,
tell the user to fix the cause and rerun initialization, and preserve all
existing files on retry. Return without starting a flow.
