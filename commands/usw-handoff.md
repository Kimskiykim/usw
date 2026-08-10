---
description: Save the current developer-local USW handoff.
---

Save the current developer-local work state. Invoke the installed
`usw-manage-handoff` skill in save mode for the exact current operation and
follow its instructions. If the user asks to clear all finished work or passes
`cleanup`, use cleanup mode; it removes only `completed` and `failed`
operations. If the user asks to finish one operation, use finish mode with its
exact ID. Treat other command arguments as selection context. With no ID,
follow the skill's zero/one/many rules and never choose among multiple
operations automatically. If handoff is disabled in `usw.yaml`, explain that
no router, operation file or candidate was read or changed. Do not reproduce
workflow logic in this command.
