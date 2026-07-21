# Review receipt: {{review_id}}

- Gate: `{{internal_or_transition}}`
- Owner role: `{{analysis_development_or_testing}}`
- Subject: `{{typed_subject}}`
- Reviewed scope: {{reviewed_scope}}
- Previous attempt or receipt: {{previous_or_none}}
- Reviewer: {{reviewer}}
- Verdict: `{{accepted_or_rejected}}`
- Timestamp: {{timestamp}}
- Evidence IDs or observed verification: {{evidence_or_verification}}
- Findings: {{findings_or_none}}

<!-- For a task subject only, add Artifact model and Contract identity. -->
<!-- For a v1 task only, also add Product source identity. -->
<!-- For a transition gate only, add Sender and Receiver; Receiver owns the receipt. -->

## Reviewed artifact identities

| Path | SHA-256 |
|---|---|
| `{{project_relative_path}}` | `{{sha256_raw_bytes}}` |
