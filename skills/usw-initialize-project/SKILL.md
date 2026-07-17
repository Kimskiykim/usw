---
name: usw-initialize-project
description: Initialize an OpenSpec-compatible USW workspace and developer-local handoff state in the current project. Use when the usw-init command delegates initialization or the user asks to initialize USW in a project.
---

# Initialize USW

Resolve `scripts/init_usw.py` relative to this `SKILL.md`, then run it with
Python 3 and pass the current project root as its only argument.

Report whether `openspec/`, `openspec/specs/`, `openspec/changes/`,
`openspec/AGENTS.md`, `.usw/.gitignore`, and `.usw/HANDOFF.md` were created or
already existed. Never overwrite an existing file. Adopt an existing OpenSpec
workspace and add only missing artifacts.

Initialize `.usw/HANDOFF.md` with no active work and treat it as the
developer's entrypoint for resuming work across local sessions. Keep `.usw/`
out of Git through its generated `.gitignore`. Treat `openspec/` as shared,
version-controlled project state.

Both `.usw/` and `openspec/` must be real directories inside the project root.
Reject symbolic links in managed paths rather than writing outside the project.

The bundled templates under `templates/change/` and `templates/task/` define
the artifact contract for future change and granular task creation. Project
initialization does not copy or instantiate those change templates.
