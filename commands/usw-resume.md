---
description: Resume work from the developer-local USW handoff.
---

Resume developer-local work. Invoke the installed `usw-manage-handoff` skill
in resume mode with an optional exact operation ID and follow its instructions.
With no ID, follow the skill's zero/one/many rules and never choose among
multiple operations automatically. Continue only after an explicit decision
for the same routed operation; never automatically retry an `in_progress`
operation. Legacy role-based state is read-only recovery context until explicit
Finish. If handoff is disabled, explain that no router or operation file was
read or changed. Do not reproduce workflow logic in this command.
