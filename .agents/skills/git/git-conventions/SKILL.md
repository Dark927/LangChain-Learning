---
name: git-conventions
description: >-
  Expert guidelines for Git branch naming and writing production-ready, conventional commit messages.
  Use this skill whenever generating branch names, committing code, or advising the user on version control practices.
---

# Git Conventions & Commit Standards Skill

This skill defines the strict, modern version control conventions required for production-ready codebases. 

---

## 1. Branch Naming Conventions

Always use descriptive, categorized branch names in lowercase, separated by hyphens (kebab-case).

### Formats:
- **`feature/<feature-name>`**: For new features or significant additions (e.g., `feature/tiered-idle-hints`).
- **`bugfix/<bug-name>`** (or `fix/<bug-name>`): For resolving issues in existing code (e.g., `bugfix/cursor-offset-crash`).
- **`chore/<chore-name>`**: For maintenance, dependency updates, or configuration changes (e.g., `chore/update-langchain-deps`).
- **`refactor/<refactor-name>`**: For code structure changes that neither fix bugs nor add features.
- **`hotfix/<hotfix-name>`**: For urgent production fixes.

---

## 2. Commit Message Header Format

Commits must follow the **Conventional Commits** specification. The header must be a single line, entirely lowercase, and written in the imperative mood (acting as a command).

**Syntax**: `type(scope): description`

- **Type**: 
  - `feat`: A new feature
  - `fix` (or `bugfix`): A bug fix
  - `chore`: Maintenance, config changes, build tasks
  - `refactor`: Code changes without feature additions or bug fixes
  - `docs`: Documentation only changes
  - `test`: Adding or correcting tests
  - `perf`: Code changes that improve performance
- **Scope**: The module, system, or component affected (e.g., `tracing-hints`, `runner`, `config`).
- **Description**: 
  - Start with a lowercase verb in the imperative mood (`implement`, `add`, `refactor`, `remove`).
  - Do not end with a period.

*Example*: `feat(tracing-hints): implement tiered idle hint system with dynamic route pointer`

---

## 3. Commit Message Body Guidelines

The body provides the detailed *what* and *why*. It must be separated from the header by a single blank line.

- Use detailed sentences starting with lowercase action verbs (`implement`, `orchestrate`, `refactor`, `update`).
- Do not use periods at the end of these descriptive lines.
- Focus on architectural decisions, the reasoning behind structural changes (e.g., SRP enforcement), and system impacts.

### Gold Standard Example

```text
feat(tracing-hints): implement tiered idle hint system with dynamic route pointer

implement tiered idle service tracking player inactivity to trigger staggered audio and visual pointer hints
orchestrate cyclic visual pointer movement that intelligently offsets from the player's current cursor progress along the stroke
refactor monolithic GameplayLevelConfigSO into modular component-specific data structs like IdleHintConfig and SilhouetteConfig
update GameInstaller to bind granular config struct instances independently to strictly enforce SRP across all visual systems
```

---

## 4. Execution Rules for the Agent
- Whenever asked to commit code, automatically format the commit message matching the gold standard above.
- If multiple different types of changes were made, encourage splitting them into separate atomic commits (e.g., one `refactor:` commit and one `feat:` commit).
