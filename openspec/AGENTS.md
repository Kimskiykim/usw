# OpenSpec workflow

Use this directory as the shared specification source of truth.

## Artifact roles

- `specs/<capability>/spec.md` describes the current accepted system behavior.
- `changes/<change-id>/proposal.md` explains why and what a change introduces.
- `changes/<change-id>/design.md` records decisions shared by the whole change.
- `changes/<change-id>/specs/<capability>/spec.md` contains specification deltas.
- `changes/<change-id>/tasks.md` is the task index and completion source of truth.
- `changes/<change-id>/tasks/<task-id>-<slug>/task.md` defines one leaf task.
- Task `development-evidence.md` and `testing-evidence.md` record role-owned proof;
  reviewer decisions live under the configured USW review root.

## Rules

1. Give every executable leaf task a stable ID that is unique within its change.
2. Keep completion checkboxes only in `tasks.md`; do not duplicate task status.
3. Link each task entry in `tasks.md` to its granular `task.md`.
4. Put task scope, non-scope, dependencies, definition of done, and verification in
   `task.md`.
5. Update change-level `design.md` when a task changes a shared technical decision.
6. Merge only specification deltas into master specs when archiving a change.
7. Keep developer-local state in `.usw/`; do not copy it into shared artifacts.

Directory detection and OpenSpec-provider initialization never create or modify
provider-owned `openspec/**`. An explicit standalone custom root remains a
user-selected writable namespace. Provider operations may validate and update
required OpenSpec artifacts only within their own scope.
