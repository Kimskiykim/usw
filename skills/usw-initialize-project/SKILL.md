---
name: usw-initialize-project
description: Initialize a configured USW workspace and developer-local handoff state in the current project. Use when the usw-init command delegates initialization or the user asks to initialize USW in a project.
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
whether to continue with LLM initialization under the same functional v1
contract. Explain that existing files will not be overwritten but execution is
less deterministic. Do not write anything until the user explicitly agrees.
After agreement, read and follow
[references/llm-fallback.md](references/llm-fallback.md). If the user declines,
stop without changes.

Report whether `usw.yaml`, configured USW roots, the five nested flow examples,
standalone project-owned artifact templates, `.usw/.gitignore`, and
`.usw/HANDOFF.md` were created or already existed. Never overwrite an existing
file. Treat a real `openspec/` directory only as a hint: detection alone never
authorizes writes. Honor any safe standalone custom root explicitly configured
under `openspec/**`; for the OpenSpec provider, leave provider-owned files
unchanged. For standalone, report the explicit provider opt-in path; when the
OpenSpec provider is already selected, report it as active without another
opt-in suggestion. New local flows and intent clarification sessions create
`.usw/flows/` and `.usw/refinements/` only on first use.

Initialize `.usw/HANDOFF.md` with no active work and treat it as the
developer's entrypoint for resuming work across local sessions. Generate
`.usw/.gitignore` as a convenience, but do not inspect or enforce Git tracking
state; repository tracking policy belongs to the user. Treat `openspec/` as
shared, version-controlled project state.

All configured roots and `.usw/` must be real directories inside the project
root. Reject symbolic links and conflicting roots before any managed write.

Capability boundary: inputs are a project root and existing configuration;
permitted writes are initialization configuration, missing managed roots,
standalone artifact templates, non-normative flow examples, and developer-local
initial state. Return the created or existing paths to the caller. Return point:
after initialization reporting. Do not start a role flow or call another skill.
If initialization fails after a partial write, report the possible partial
workspace and recommend fixing the cause and rerunning; create-only behavior
preserves existing files on retry.

The bundled templates under `templates/change/` and `templates/task/` define
the artifact contract for future change and granular task creation. For the
standalone provider, copy every missing change, task, evidence, and review
template to `<artifacts.root>/templates/`. Preserve existing project-owned
templates byte-for-byte. Do not copy templates into an OpenSpec artifact root.

The bundled files under `templates/flows/examples/` are guidance, not runtime
fallbacks or normative flow contracts. Copy exactly `analysis.md`,
`development.md`, `testing.md`, `chat-review.md`, and `dev-test.md` to
`<flows.root>/examples/`. Never create, migrate, or delete legacy
`flow-scenario-*.md` files.
