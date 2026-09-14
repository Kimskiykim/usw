## Context

Two symptoms, one cause. `handoff_state.py` imports `fcntl` at module level, so
on Windows every handoff transition — and therefore every flow run under the
default `handoff: true` — dies before doing anything. `run_flow.py` refuses
packaged flows and packaged resources on Windows with
`unsupported_safe_flow_platform`, leaving only the compatible flat layout, so
even the half that appears to work excludes the canonical layout for new flows.

Underneath both: USW's safe filesystem boundary is POSIX descriptor-relative
access — `dir_fd`, `O_NOFOLLOW`, `O_DIRECTORY`, `flock`, `fstat`, `fchmod`.
`os.supports_dir_fd` is empty on Windows and none of the rest exists there.

The good news, measured rather than assumed: in `handoff_state.py` this is
concentrated in four primitives — `_locked_local_directory`,
`_opened_operation_directory`, `_read_regular_at` and `_atomic_write` — plus
seven call sites that thread descriptors between them. It is not spread through
the file's 1744 lines. That is what makes wrapping viable instead of rewriting,
and it is why the plan below routes call sites through a boundary rather than
converting them one by one.

`/usw-init` succeeds on Windows because `init_usw.py` happens not to use any of
this, which is what produces the worst symptom: the tool installs, initializes
cleanly, and fails on the user's first real action.

No specification declares a supported platform. Today's behavior was never
decided; it is what the implementation happened to do.

Verification constraint: this work cannot be validated on the development
machine. Existing tests simulate Windows by patching
`_uses_windows_path_fallback`, which exercises branch selection but not
`msvcrt`, not reparse points, and not Windows path semantics. Only a
`windows-latest` CI job actually tests the platform.

## Goals / Non-Goals

**Goals:**

- Windows runs every documented capability, including routed handoff and both
  flow layouts.
- One safe-access boundary, so component behavior does not fork per platform.
- The POSIX guarantee is preserved exactly as it is today.
- The weaker Windows guarantee is stated wherever safety is described.
- The platform is verified by CI rather than asserted.

**Non-Goals:**

- Guarantee parity between platforms. It is not reachable with what Python
  exposes on Windows.
- Any change to flow semantics, statuses, authority, or permission boundaries.
- Rewriting the POSIX implementation. It stays; it is wrapped.

## Decisions

### One boundary, two backends — not two code paths per call site

A shared safe-access module exposes the operations both scripts need: open a
contained directory, open a child directory, read a regular file, write a file
atomically, and stat without following links. It selects a backend once, by
capability probe (`os.supports_dir_fd`), not by `os.name`.

Alternatives considered. Scattering `if windows:` at each of the dozens of call
sites was rejected: it multiplies the number of places a platform can diverge
silently, and the current single divergence already produced a two-year-invisible
break. Rewriting everything to pathname access on all platforms was rejected
because it would discard a working guarantee on the platforms that can hold it,
to buy uniformity nobody asked for.

Probing capability rather than branching on `os.name` matters because the
property that actually decides the implementation is "does `dir_fd` work here",
and a probe states that directly.

### Windows locking: an explicit lock file, not the state directory

POSIX locks the `.usw` directory descriptor. Windows cannot open a directory with
`os.open`, so the Windows backend locks a dedicated `.usw/.lock` file with
`msvcrt.locking`, acquired with a bounded retry rather than an unbounded block, so
a stuck holder surfaces as a handoff error instead of a hang.

The lock file is state, not content: it is never read, never migrated, and its
absence is not an error worth reporting to a user — it is created on demand.

### Windows traversal: reject reparse points per component, re-verify containment

Windows has no `O_NOFOLLOW`. The backend walks each component, rejects anything
carrying `FILE_ATTRIBUTE_REPARSE_POINT` — which covers symlinks and junctions,
the latter being the case a naive `islink()` check misses — and re-verifies that
the fully resolved path is still contained in the root before the final open.

This narrows the swap window; it does not close it. That is the honest limit and
it is written into the specification rather than left for someone to discover.

### Accepting the weaker guarantee, and why it is proportionate here

The descriptor-relative design defends against an attacker who can swap a path
component between the check and the use. To reach `.usw/` or a flow root, that
attacker already has write access to the user's project — at which point editing
`FLOW.md` directly is simpler and equally effective, and no descriptor discipline
prevents it. The guarantee is therefore worth keeping where it is free, and not
worth refusing the platform over.

What would be unacceptable is silence. A user comparing platforms must be able to
learn that one backend is weaker without reading the source, which is why
disclosure is a requirement and not a comment.

### CI: land the Windows job early, non-blocking, then make it blocking

The job is added at the start of the work with `continue-on-error`, so progress is
visible on the only platform that can actually report it, and the flag is removed
in the final task once the suite passes. A Windows job added only at the end would
mean writing the whole change blind.

## Risks / Trade-offs

- **This cannot be verified locally.** → The Windows job lands first, and no task
  is considered done on the strength of a simulated-Windows unit test alone.
- **Converting a well-tested safety boundary risks a subtle regression**, even
  though the surface is four primitives rather than the whole file. → Route every
  call through the boundary without changing the POSIX behavior underneath, and
  keep the existing POSIX tests as the regression net.
- **Windows path semantics differ** — case-insensitivity, reserved names, path
  length, `\` separators. → Containment checks compare resolved paths rather than
  strings, and the Windows job exercises them for real.
- **Reparse-point checks can be wrong in a way that only shows on Windows.** →
  Cover them in the Windows job explicitly, not only through the shared suite.
- **Scope is large enough to hide a second problem.** → Phase the work so handoff,
  which is what actually breaks every run, lands and is verified before flow
  resolution is touched.

## Migration Plan

Additive and behavior-preserving on POSIX: existing projects see no change, and
`.usw/.lock` appears only on Windows. Rollback is reverting to the POSIX-only
implementation, which restores today's behavior including its Windows break.

The phases are independently shippable. After phase 2, Windows users can run
flows with handoff. After phase 3, they can also use packaged flows.

## Open Questions

- Whether `msvcrt.locking` on a lock file is sufficient for the multi-process
  case USW actually has, or whether the bounded retry needs tuning, cannot be
  settled here — it is a question for the Windows job under real contention.
- Whether any USW user runs on a POSIX platform where `os.supports_dir_fd` is
  unexpectedly empty is unknown; the probe handles it by falling back, which is
  safe but silently weaker, so the fallback logs which backend it selected.
