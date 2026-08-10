# Flow: unsafe-repeat

Deploy a release, which is an irreversible external write.

- If deployment succeeds, return `completed`.
- If deployment fails, repeat the deployment with no attempt limit and no
  idempotency guarantee.
