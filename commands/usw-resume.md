---
description: Resume work from the developer-local USW handoff.
---

Resume the current developer-local work. Invoke the installed
`usw-manage-handoff` skill in resume mode and follow its instructions. Continue
from saved generic context only after an explicit decision for the same
operation. Never automatically retry an `in_progress` operation. Legacy
role-based state is read-only recovery context until explicit finish. If
handoff is disabled, explain that no state was read or changed. Do not reproduce
workflow logic in this command.
