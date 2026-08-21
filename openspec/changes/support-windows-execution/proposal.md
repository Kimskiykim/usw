## Why

USW does not run on Windows, and it fails in the worst possible way: `/usw-init`
succeeds, then the first flow run aborts before executing anything. With the
default `handoff: true`, every run calls `handoff_state.py`, whose module-level
`import fcntl` raises `ModuleNotFoundError` on a platform that has no such
module. Flow resolution is affected too — packaged `<name>/FLOW.md`, the
canonical layout for new flows, is rejected on Windows with
`unsupported_safe_flow_platform`, leaving only the compatible flat layout.

Underneath both is one cause: every safe filesystem boundary in USW is built on
POSIX descriptor-relative access — `dir_fd`, `O_NOFOLLOW`, `O_DIRECTORY`,
`flock`. `os.supports_dir_fd` is empty on Windows, so none of it exists there.

No specification states which platforms USW supports. The current behavior is an
emergent property of the implementation, never a decision anyone recorded.

## What Changes

- Declare the supported platforms explicitly, so platform behavior stops being
  emergent.
- Introduce one safe-access boundary with two backends: the existing POSIX
  descriptor-relative implementation, unchanged, and a Windows implementation
  that rejects reparse points per component and re-verifies containment.
- State plainly, in specification and in documentation, that the Windows backend
  provides a weaker guarantee against a concurrent attacker than the POSIX one,
  and why that is accepted.
- Make routed handoff work on Windows: a cross-platform lock, and safe state
  reads and writes that do not require `dir_fd`.
- Make flow resolution work on Windows for both layouts, including packaged
  flows and their resources, removing `unsupported_safe_flow_platform` as the
  normal outcome there.
- Add a `windows-latest` job so the platform is verified rather than assumed.

## Capabilities

### New Capabilities

- `cross-platform-safe-access`: Defines the supported platforms, the single safe
  filesystem boundary used by every component, its two backends, the guarantee
  each provides, and the requirement that a weaker guarantee is disclosed rather
  than silently substituted.

### Modified Capabilities

- `live-operation-state`: Routed handoff operates on every supported platform,
  and its serialization no longer depends on POSIX-only locking.
- `text-flow-execution`: Safe resolution of both flow layouts, and of packaged
  resources, works on every supported platform.

## Impact

- `skills/usw-manage-handoff/scripts/handoff_state.py`, whose safe access is
  built on `dir_fd` throughout its 1744 lines.
- `skills/usw-run-flow/scripts/run_flow.py`, including the removal of
  `unsupported_safe_flow_platform` as the ordinary Windows outcome.
- A shared safe-access module used by both, and its tests.
- `.github/workflows/ci.yml`, which gains a `windows-latest` job.
- README and skill instructions, which must state the platform difference.
- No new dependency and no change to what any flow is permitted to do.

## Non-Goals

- Parity of the concurrent-attacker guarantee between platforms. It is not
  achievable with what Python exposes on Windows, and pretending otherwise would
  be worse than stating the difference.
- Support for platforms outside the declared set.
- Any change to flow semantics, statuses, or permission boundaries.
