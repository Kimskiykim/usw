---
description: Save the current developer-local USW handoff.
---

Save the current developer-local work state. Invoke the installed
`usw-manage-handoff` skill in save mode and follow its instructions. If the user
explicitly asks to finish or clear the task, use the skill's finish mode. Treat
any command arguments as context for the handoff. If handoff is disabled in
`usw.yaml`, explain that no state was read or changed. Finish is the only action
allowed to replace a non-idle state with idle. Do not reproduce workflow logic
in this command.
