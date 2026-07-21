# OpenSpec compatibility

`openspec-version.txt` is the single release-blocking version source. The
`pinned` runner installs exactly that version and propagates every scenario
failure. The separate `latest` runner resolves and prints the current published
version and propagates its real result; CI marks only that job `continue-on-error`
so the failure remains visible without changing the pinned release gate.

Promoting latest is intentional: update `openspec-version.txt` in a reviewed
change, run `./tests/run_openspec_compatibility.sh pinned`, and accept the new
target only with successful compatibility evidence. The probe never edits the
pinned source automatically.
