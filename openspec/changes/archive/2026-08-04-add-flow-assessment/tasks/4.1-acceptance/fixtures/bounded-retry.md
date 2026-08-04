# Flow: bounded-retry

Attempt the read-only check at most three times.

- If an attempt succeeds, return `completed`.
- After the third failed attempt, return `failed`.
