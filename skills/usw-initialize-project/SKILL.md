---
name: usw-initialize-project
description: Initialize a standalone USW workspace and developer-local handoff state in the current project. Use when the usw-init command delegates initialization or the user asks to initialize USW in a project.
---

# Initialize USW

Resolve `scripts/init_usw.py` relative to this `SKILL.md`. Select its
interpreter before making any project write:

1. Try `python3`, then `python`.
2. For each candidate, run
   `<candidate> -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'`.
3. Use the first candidate that exits successfully and pass the current project
   root as the script's only argument.
4. Treat any non-zero result from `init_usw.py` as an initialization failure.
   Report it and stop; never hide a script or configuration error with fallback.

If neither command provides Python 3.10 or newer, ask the user in their language
whether to continue with limited LLM initialization. Explain that existing
files will not be overwritten but deterministic safety checks are weaker. Do
not write anything until the user explicitly agrees. After agreement, read and
follow [references/llm-fallback.md](references/llm-fallback.md). If the user
declines, stop without changes.

Report whether `usw.yaml`, configured standalone roots, project-owned artifact
templates, `.usw/.gitignore`, and `.usw/HANDOFF.md` were created or already
existed. Never overwrite an existing file. If an OpenSpec workspace exists,
report the explicit provider opt-in path and leave every OpenSpec file unchanged.
New intent clarification sessions create `.usw/refinements/` on first use.
Treat an existing `refinement.root` as a legacy diagnostic only: report its
exact path and never create, move, or rewrite it.

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
