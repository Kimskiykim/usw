---
name: usw-initialize-project
description: Initialize the USW harness in the current project by creating usw/SYNC.md and hello_world.py. Use when the usw-init command delegates initialization or the user asks to initialize USW in a project.
---

# Initialize USW

Resolve `scripts/init_usw.py` relative to this `SKILL.md`, then run it with
Python 3 and pass the current project root as its only argument.

Report whether `usw/SYNC.md` and `hello_world.py` were created or already
existed. Never overwrite an existing file.
