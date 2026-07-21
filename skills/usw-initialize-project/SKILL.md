---
name: usw-initialize-project
description: Initialize a standalone USW workspace and developer-local handoff state in the current project. Use when the usw-init command delegates initialization or the user asks to initialize USW in a project.
---

# Initialize USW

Resolve `scripts/init_usw.py` relative to this `SKILL.md`, then run it with
Python 3 and pass the current project root as its only argument.

Report whether `usw.yaml`, configured standalone roots, project-owned artifact
templates, `.usw/.gitignore`, and `.usw/HANDOFF.md` were created or already
existed. Never overwrite an existing file. If an OpenSpec workspace exists,
report the explicit provider opt-in path and leave every OpenSpec file unchanged.

Initialize `.usw/HANDOFF.md` with no active work and treat it as the
developer's entrypoint for resuming work across local sessions. Keep `.usw/`
out of Git through its generated `.gitignore`. Treat `openspec/` as shared,
version-controlled project state.

All configured roots and `.usw/` must be real directories inside the project
root. Reject symbolic links and conflicting roots before any managed write.

Capability boundary: inputs are a project root and existing configuration;
permitted writes are initialization configuration, missing managed roots,
standalone artifact templates, standard scenario seeds, and developer-local
initial state. Return the created or existing paths to the caller. Return point:
after initialization reporting. Do not start a role flow or call another skill.

The bundled templates under `templates/change/` and `templates/task/` define
the artifact contract for future change and granular task creation. For the
standalone provider, copy every missing change, task, evidence, and review
template to `<artifacts.root>/templates/`. Preserve existing project-owned
templates byte-for-byte. Do not copy templates into an OpenSpec artifact root.
