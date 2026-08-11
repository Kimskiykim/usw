#!/usr/bin/env python3
"""Render the human transfer note and validation report from validator JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def bullets(values: list[str]) -> str:
    return "\n".join(f"- {value}" for value in values)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--included-scope", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    if report.get("status") != "passed":
        raise SystemExit("validation report is not passed")
    stem = Path(report["bundle"]).stem
    args.output_dir.mkdir(parents=True, exist_ok=True)
    note = f"""# Transfer note: {stem}

- Bundle: `{Path(report['bundle']).name}`
- Direction: `{report['direction']}`
- Source range: `{report['base']}..{report['head']}`
- Internal target: `{report['internal_target']}`
- Internal baseline: `{report['internal_baseline']}`
- Included scope: {args.included_scope}
- Bundle SHA-256: `{report['bundle_sha256']}`

## Excluded changes

{bullets(report['excluded_changes'])}

## Handoff

No transfer or target-side apply was performed. Deliver this bundle and note to the authorized human recipient; keep bundles from different source repositories separate.
"""
    validation_lines = "\n".join(f"- {check}: {report['check_results'][check]}" for check in report["checks"])
    validation = f"""# Validation report: {stem}

- Status: `{report['status']}`
- Mode: `{report['mode']}`
- Bundle bytes: `{report['bundle_bytes']}`
- Bundle SHA-256: `{report['bundle_sha256']}`
- Embedded patch SHA-256: `{report['embedded_patch_sha256']}`
- Validation baseline: `{report['validation_baseline']}`

## Checks

{validation_lines}

## Changed files

{bullets(report['changed_files'])}

## Excluded changes

{bullets(report['excluded_changes'])}
"""
    (args.output_dir / f"{stem}-transfer-note.md").write_text(note, encoding="utf-8")
    (args.output_dir / f"{stem}-validation-report.md").write_text(validation, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
