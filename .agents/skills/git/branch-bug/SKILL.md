---
name: branch-bug
description: Creates a new bugfix branch and checks it out.
---
# Bugfix Branch Automation Skill

This skill automates the creation of a new Git bugfix branch according to our strict naming conventions.

## Execution Rules:
When this skill is activated (e.g., the user types `/branch-bug [bug-name]`), you must immediately:
1. Extract the `[bug-name]` from the user's prompt.
2. Format the name strictly into `kebab-case` (lowercase words separated by hyphens).
3. Open a terminal and run: `git checkout -b bugfix/<bug-name>`
4. Confirm to the user that the branch was successfully created and checked out.
