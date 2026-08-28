---
name: branch-feat
description: Creates a new feature branch and checks it out.
---
# Feature Branch Automation Skill

This skill automates the creation of a new Git feature branch according to our strict naming conventions.

## Execution Rules:
When this skill is activated (e.g., the user types `/branch-feat [feature-name]`), you must immediately:
1. Extract the `[feature-name]` from the user's prompt.
2. Format the name strictly into `kebab-case` (lowercase words separated by hyphens).
3. Open a terminal and run: `git checkout -b feature/<feature-name>`
4. Confirm to the user that the branch was successfully created and checked out.
