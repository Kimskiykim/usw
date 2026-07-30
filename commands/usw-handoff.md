---
description: Save the current developer-local USW handoff.
---

Save the current developer-local work state. Invoke the installed
`usw-manage-handoff` skill in save mode for the exact current operation and
follow its instructions. If the user explicitly asks to finish or clear an
operation, use the skill's finish mode with its exact ID. Treat command
arguments as selection context. With no ID, follow the skill's zero/one/many
rules and never choose among multiple operations automatically. If handoff is
disabled in `usw.yaml`, explain that no router, operation file or candidate was
read or changed. Do not reproduce workflow logic in this command.
