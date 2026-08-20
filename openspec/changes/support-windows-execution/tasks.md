## 1. Verification before implementation

- [x] 1.1 Add a `windows-latest` job to `.github/workflows/ci.yml` running the deterministic suite on the supported Python floor and latest, marked `continue-on-error` so the work is visible without blocking; record the first observed failure list as the starting baseline.
- [x] 1.2 Add a deterministic test asserting that every module a skill invokes imports successfully with `fcntl` absent from `sys.modules`, so the import-time break cannot return unnoticed on any platform.

## 2. Safe-access boundary and the handoff break

- [x] 2.1 Add failing tests for the boundary's contract on the descriptor-relative backend: contained directory open, child directory open, regular-file read, atomic write, and rejection of a link, an escape and an unexpected filesystem type; verify they pass against the existing POSIX behavior.
- [x] 2.2 Extract the shared safe-access module with a backend selected by probing `os.supports_dir_fd`, wrapping today's POSIX implementation without changing it; verify the existing suite is unchanged on POSIX.
- [x] 2.3 Add the pathname-based backend: per-component reparse-point rejection covering junctions as well as symlinks, containment re-verified against the resolved path, and no link followed at the final open; verify its rejections match the POSIX backend's errors exactly.
- [x] 2.4 Replace the module-level `fcntl` import and `_locked_local_directory` in `handoff_state.py` with the boundary's lock: `flock` where available, `msvcrt.locking` on a dedicated `.usw/.lock` with a bounded retry otherwise; a lock that cannot be acquired must fail with a handoff error rather than proceed. Landed ahead of 2.1-2.3 because it is the break that stops every run; the lock currently lives in `handoff_state.py` and moves into the shared boundary at 2.2. Backend selection probes `os.supports_dir_fd` and the presence of `fcntl` rather than `os.name`.
- [x] 2.5 Route every `dir_fd` call site in `handoff_state.py` through the boundary; verify the complete suite passes on POSIX with no behavior change.
- [ ] 2.6 Confirm on the Windows job that Begin, Outcome, Save, Resume, Finish and Cleanup all complete, and record the observed results.

## 3. Flow resolution on every platform

- [x] 3.1 Add failing tests that a packaged `<name>/FLOW.md` and a packaged resource resolve through the pathname-based backend with the same name, origin, identity, path, flow directory and exact bytes as the descriptor-relative one.
- [x] 3.2 Route `run_flow.py` traversal, entrypoint read and resource read through the boundary, and remove `unsupported_safe_flow_platform` as the ordinary outcome for a supported platform; keep it only for a platform outside the declared set.
- [x] 3.3 Remove `_load_windows_flat_flow` and `_uses_windows_path_fallback` once the boundary covers both layouts, and update the tests that simulate Windows by patching that predicate so they exercise the backend instead.
- [ ] 3.4 Confirm on the Windows job that both layouts, packaged resources, and the ambiguity and symlink rejections behave identically to POSIX, and record the observed results.

## 4. Disclosure and closing

- [x] 4.1 Document the guarantee difference where safety is described: the safe-access module, the runner and handoff skill instructions, and the README platform section. State what the pathname-based backend does not prevent, without describing the two as equivalent.
- [ ] 4.2 Remove `continue-on-error` from the Windows job so the platform becomes a real gate; verify the workflow is red when the suite fails there.
- [x] 4.3 Record which backend was selected in the harness of the deterministic suite output, so an unexpectedly weaker backend on a POSIX platform is visible rather than silent.
- [ ] 4.4 Run the complete suite on the supported Python floor and latest, `openspec validate --all --strict`, `openspec status --change support-windows-execution --json` and `git diff --check`, and record each command with its result.

## Progress evidence

Recorded 2026-08-20 on macOS/arm64. Windows itself is NOT verified: the
`windows-latest` job has not run yet, and nothing below proves the platform works.

- `python3 -m unittest discover -s tests` — 216 tests, OK on Python 3.10 and 3.11,
  unchanged from the 208-test baseline. POSIX behavior is untouched: the
  descriptor-relative branch is still selected and still locks the `.usw`
  directory descriptor.
- `python3 -m unittest tests.test_platform_support` — 8 tests, OK. Covers import
  without `fcntl`, import without `msvcrt`, lock-file selection, the missing
  workspace error, bounded-retry failure under contention, and capability-probe
  selection.
- The import probe raises `ModuleNotFoundError` rather than `ImportError`: stdlib
  guards catch only the subclass, so the broader exception produced a false
  failure in `subprocess` instead of testing the target module.

### Second slice: handoff no longer needs descriptors

The safe-access boundary landed as `_SafeDirectory` with two backends,
`_DescriptorDirectory` and `_PathnameDirectory`, selected by
`open_safe_directory`. Because the handle is threaded exactly where the integer
descriptor used to be, only the five functions that actually touched the
filesystem changed; the dozens that merely pass it along were untouched.

More of this is verifiable here than expected: `_PathnameDirectory` is ordinary
path handling, so it runs on POSIX. Only the Windows reparse-point attribute
cannot be reproduced. That allowed the whole routed cycle — Begin, Outcome,
Finish — to be exercised through the pathname backend on this machine.

- `python3 -m unittest discover -s tests` — 224 tests, OK on Python 3.10 and 3.11.
- `python3 -m unittest tests.test_platform_support` — 16 tests, OK: imports without
  `fcntl` and without `msvcrt`, lock-file selection, bounded-retry contention,
  read/write/replace/unlink on the pathname backend, rejection of a symlinked
  file, a symlinked directory, a wrong filesystem type, names crossing a
  directory boundary, and a full Begin/Outcome/Finish cycle without descriptors.
- Variables that hold a handle were renamed off `descriptor`; no stale name
  remains past the backend classes.

Two test defects were found and fixed in the tests, not the code: the import
probe raised `ImportError` where stdlib guards catch only `ModuleNotFoundError`,
and the empty router was asserted by its bare marker rather than its rendered
table row.

Not verified: Windows itself. The `windows-latest` job has not run. Task 2.6
remains open and nothing here proves the platform works — only that the code no
longer requires the primitive Windows lacks.

### Third slice: flow resolution on every platform

The safe-access boundary moved into
`skills/usw-initialize-project/scripts/safe_access.py` and is loaded by both
`handoff_state.py` and `run_flow.py` under one cached module name, so a single
module object serves the whole process. Behavior is always reached through that
module rather than through re-exported aliases; otherwise patching or probing it
in one place would not hold in the other, which a test caught immediately.

`run_flow.py` now resolves both layouts and packaged resources through the
boundary. `_uses_windows_path_fallback`, `_load_windows_flat_flow` and the
ordinary use of `unsupported_safe_flow_platform` are gone, and the two legacy
branches of `_legacy_flow_warning` collapsed into one.

The three tests that asserted Windows fails closed were replaced rather than
deleted: they now force the pathname backend and assert it produces the *same*
identity, path, flow directory and bytes as the descriptor backend, and that
symlink and ambiguous-layout rejections still hold there.

- `python3 -m unittest discover -s tests` — 226 tests, OK on Python 3.10 and 3.11.
- Documentation updated: `skills/usw-run-flow/SKILL.md` and a new README platform
  section state which backend is weaker and what it does not prevent.

One defect of my own: removing `_load_windows_flat_flow` by slicing to the next
`def` also removed the `@contextmanager` decorator of the function after it. The
suite caught it immediately with a clear error.

Ordering note for archiving: `support-packaged-flows` also modifies the
`text-flow-execution` requirement and still says packaged flows stop with
`unsupported_safe_flow_platform` on Windows. Archive that change first, then this
one, or the older text will overwrite the newer.

### Fourth slice: the selected backend is visible

A silent downgrade would quietly weaken safety on a platform that could hold the
stronger guarantee, so selection is now asserted rather than logged: a platform
whose `os.supports_dir_fd` is non-empty and which has `fcntl` must select
`DescriptorDirectory`, and any other outcome fails the suite. The backend name is
also printed once per run, so every suite states which one it exercised.

Acceptance as of this slice, on macOS/arm64:

- `python3 -m unittest discover -s tests` — 228 tests, OK on Python 3.10 and 3.11;
  reports `safe-access backend: DescriptorDirectory`.
- `openspec validate --all --strict` — 17 of 17 items valid.
- `git diff --check` — exit 0.

Still open and not claimable here: 2.6 and 3.4 require the `windows-latest` job to
actually run, and 4.2 must not remove `continue-on-error` before it does. The job
exists and triggers on pushes to `dev/**` and on pull requests, but nothing has
been committed or pushed, so it has never executed. Every Windows statement in
this change remains unverified on Windows.
