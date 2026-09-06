## Context

Production flow resolution currently accepts one kebab-case selector and opens
only `<flow-root>/<name>.md`. The safe loader holds directory descriptors while
traversing the configured root and reading the final file, while finder and
authoring contracts independently assume that all runnable flows are direct
Markdown entries. A package layout must therefore change resolution, discovery,
authoring, assessment, and their documentation together without weakening the
existing containment and no-symlink boundary.

## Goals / Non-Goals

**Goals:**

- Make `<flow-root>/<name>/FLOW.md` the canonical layout for new flows.
- Give packaged Markdown a stable base for `scripts/`, `references/`, `assets/`,
  and other explicitly referenced resources.
- Preserve execution and editing of existing `<flow-root>/<name>.md` flows.
- Keep one kebab-case selector and the existing local-first origin semantics.
- Keep discovery bounded and every entrypoint read descriptor-relative.

**Non-Goals:**

- Arbitrary recursive namespaces or selectors containing `/`.
- Automatic loading, hashing, indexing, or execution of every package resource.
- Migration of existing flat flows.
- A manifest, package registry, dependency manager, parser, or new authority.

## Decisions

### Use a fixed `FLOW.md` entrypoint

The package name is its direct child directory name and its only entrypoint is
`FLOW.md`. This matches the skill-like ownership model without duplicating the
name as `<name>/<name>.md`. Arbitrary filenames inside a package were rejected
because they require another selector or manifest and make bounded discovery
less deterministic.

### Keep selectors flat and resolve layouts within one origin

`review` remains the selector for either `review.md` or `review/FLOW.md`. The
resolver checks one origin at a time. If both entrypoints exist safely in that
origin it returns `ambiguous_flow_layout`; it never selects one by precedence.
Only a missing local flow permits the existing fallback to shared. Allowing
slash-separated selectors was rejected because it turns packages into an
unbounded namespace and expands traversal validation unnecessarily.

### Preserve descriptor-relative entrypoint loading

The loader opens the selected flow root once. A flat entrypoint is read from
that descriptor as today. A packaged entrypoint requires opening the direct
`<name>` directory with no-follow directory flags and then `FLOW.md` with
no-follow regular-file checks. The returned flow gains an exact absolute
`flow_directory`: the flow root for a flat flow and the package directory for a
packaged flow.
`path` remains the exact entrypoint path and identity remains derived from the
same entrypoint bytes and origin as before.
On Windows, where this Python runtime lacks descriptor-relative traversal, the
pre-existing flat-flow pathname fallback remains compatible. Packaged
entrypoints and package resources fail closed with
`unsupported_safe_flow_platform` instead of extending that weaker fallback to
new paths.

### Treat package-relative resources as explicit dependencies

The model receives a resolver-owned absolute `flow_directory` separately from
immutable Markdown and user input. A relative resource named in packaged
`flow_markdown` is interpreted from that directory; the same text supplied only
through `user_input` is not a package dependency. Absolute paths, `..` escape,
and discovered symlink traversal are rejected at the use boundary. The resource
boundary derives its base from the resolved invocation rather than accepting a
caller-supplied directory. At explicit use, the runner opens the final regular
file with no-follow flags through the held package descriptor and returns its
immutable bytes plus a separate resource identity. `resource_path` is reporting
metadata and MUST NOT be reopened. Resources remain ordinary text-first
executor dependencies and normal permission checks still apply when returned
bytes are interpreted or executed. Bundling a script grants no authority and
does not add its bytes to flow identity.

Compatible flat flows receive `flow_directory` as invocation metadata, but
their existing relative references retain their prior project/workspace-relative
interpretation. This avoids silently rebasing existing Markdown when the feature
is installed.

### Make packages the authoring default without rewriting legacy flows

Creating a previously absent flow writes `<name>/FLOW.md`. Updating a flow first
resolves its existing layout and writes the same entrypoint. Immediately before
the write, authoring rechecks both candidate entrypoints and every package path
component without following symlinks; a new alternate entrypoint, unsafe target,
or changed target stops the write. A safe pre-existing `<name>` directory may be
used without modifying its other contents. If both layouts exist, authoring
stops with the same ambiguity error. This avoids a migration flag and keeps old
project-owned paths stable.

### Discover only direct flat entries and direct packages

Finder enumerates direct `*.md` files and direct kebab-case directories that
contain `FLOW.md`, then loads plausible candidates through the shared resolver.
It does not recurse into package resource directories. Assessment continues to
consume only immutable resolver output, reports the selected `flow_directory`,
and never opens sibling package resources; explicitly named resources remain
unverified dependencies in semantic assessment.

### Keep prompt verification claims narrow

`usw-create-flow`, `usw-find-flow`, and `usw-assess-flow` are text-first model
skills, not deterministic Python executors. Repository substring tests verify
their instruction contracts only; they do not prove model behavior. Resolver
and CLI scenarios remain deterministic runtime tests. End-to-end model-behavior
evaluation requires a separate LLM eval harness and is outside this change.

## Risks / Trade-offs

- [Two supported layouts increase resolver branches] → Keep one selector and a
  single shared resolver, with explicit flat/package/ambiguous tests.
- [A package resource can change after entrypoint loading] → Read its exact
  bytes through held descriptors only at explicit use, return a separate
  resource identity, and never reopen the report-only pathname.
- [Generic editor tabs all show `FLOW.md`] → Report and expose the package path;
  avoid duplicating names solely for editor convenience.
- [An existing same-name directory may be mistaken for an incomplete package]
  → A package is runnable only when it contains `FLOW.md`; creation preserves
  existing safe directory contents and writes only the requested entrypoint.

## Migration Plan

No eager migration is required. Existing flat flows remain runnable and are
edited in place; newly created flows use packages. Rollback consists of moving a
package entrypoint to `<name>.md` after first rewriting any package-relative
resource references, then using the previous USW release. The feature itself
does not delete or relocate user files.

## Open Questions

None.
