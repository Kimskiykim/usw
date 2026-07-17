---
name: usw-manage-handoff
description: Save, finish, validate, or resume developer-local work through .usw/HANDOFF.md. Use when /usw-handoff or /usw-resume delegates its workflow, or when the user asks to checkpoint current work, preserve context before a pause, finish the local task state, recover work in a new session, or continue from a saved handoff.
---

# Manage USW Handoff

Resolve `scripts/handoff_state.py` relative to this `SKILL.md`. Treat
`.usw/HANDOFF.md` as mutable developer-local state, never as a shared project
artifact or historical journal.

Find the nearest Git root from the current directory. If `.usw/HANDOFF.md` is
missing, stop and tell the user to run `/usw-init`.

## Save

Use save mode for `/usw-handoff` unless the user explicitly asks to finish or
clear the active work.

1. Inspect the current work and record only factual state. Separate completed
   actions from plans. Record commands actually run and their results; otherwise
   write `- Not run.`.
2. Write `.usw/HANDOFF.next.md` with this exact structure:

```markdown
# Developer Handoff

- Updated: <ISO 8601 timestamp with timezone>
- Status: in_progress | paused | blocked
- Task: <short task description>

## Done

- <completed fact, or Nothing yet.>

## Changed areas

- `<path>`, or None.

## Verification

- `<command>` -> passed | failed

## Risks / blockers

- <risk or blocker, or None known.>

## Next action

One concrete, verifiable next action on one line.

## References

- <canonical path or URL, or None.>
```

Do not add `## Source snapshot`: the script removes any candidate-supplied
copy and appends its own compact, trusted fingerprint during `save`.

3. A `passed` or `failed` verification is valid only when it applies to the
   source immediately before `save`. If source changed afterwards or this is
   uncertain, rerun the check or write `- Not run.`. Keep exactly one current
   state; do not append previous sessions or completed handoffs, or copy
   referenced specifications into it.
4. Run:

```text
python3 <skill-dir>/scripts/handoff_state.py save <project-root> <project-root>/.usw/HANDOFF.next.md
```

5. Report the saved status and next action. The generated snapshot contains
   hashes only; it never stores source content or a diff.

If the user explicitly finishes or clears the task, run:

```text
python3 <skill-dir>/scripts/handoff_state.py finish <project-root>
```

## Resume

1. Run:

```text
python3 <skill-dir>/scripts/handoff_state.py show <project-root>
```

2. If the state is `idle`, report that no work is available to resume and stop.
3. Read referenced local artifacts only as needed. Report missing references;
   never invent their contents or silently create replacements.
4. Use the `freshness` reported by `show`: `fresh` means the saved source still
   matches, `stale` means it changed, and `unknown` means a reliable comparison
   was not possible. A branch/ref warning by itself does not make verification
   stale. Briefly state the task, saved verification, risks, and next action.
5. Continue from `Next action` when it remains applicable and is within the
   user's existing scope. If it is stale, unknown, or blocked, explain the
   concrete mismatch before selecting another action.
