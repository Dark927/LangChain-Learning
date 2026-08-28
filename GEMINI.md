# Project Rules & Agent Execution Bridge

These rules govern all agent behaviors, coding standards, architectural decisions, and skill activations across this workspace.

---

## 1. Core Principles
- **No Unsolicited Visualizers**: Do not create visualizers or debugging visual tools unless explicitly asked.
- **Clean Production Comments**: Do not write comments explaining your actions or reasoning in the code. Production code must use clear English comments explaining logic and purpose only.
- **Preserve Existing Code**: Do not modify or overwrite existing working scripts unless explicitly instructed by the user.
- **YOLO Git Execution**: Whenever requested to perform Git operations (commits, branching, pushes, merges), execute the terminal commands immediately and autonomously without asking for permission first.

---

## 2. Hardcoding Rules
- **No Magic Numbers or Raw Strings**: Do not use magic numbers or raw strings directly in logic blocks.
- **Constants & Fields**: Create fields/constants for numbers and strings used within the class or module.

---

## 3. Unity C# Conventions

### Naming Conventions
- **Private fields**: Use the `m_` prefix followed by PascalCase (e.g., `m_TargetSpeed`).
- **Public fields, properties, and events**: Use PascalCase (e.g., `TargetHealth`).
- **Events**: Prefix with `On` (e.g., `OnHealthChanged`).
- **Parameters and local variables**: Use camelCase (e.g., `currentDamage`).

### Documentation Rules (XML Comments)
Provide clear, functional English XML comments on:
- Classes and Interfaces
- Public Fields and Properties
- Events
- Public Methods and Interface Implementations (include `<param>` and `<returns>` tags whenever applicable)

### Code Organization (`#region` Blocks)
Group class members strictly using `#region` blocks in this exact order:
1. `Serialized Fields`
2. `Public Fields`
3. `Public Properties`
4. `Events`
5. `Private Fields`
6. `Unity Lifecycle Methods`
7. `[InterfaceName] Implementation` (Replace with actual interface name if applicable)
8. `Public API Methods`
9. `Private Helper Methods`
10. `Debug Visualization` (Wrapped in `#if UNITY_EDITOR` / `#endif`)

---

## 4. Python & Agentic AI Guidelines

### Architecture & SOLID Principles
- **Single Responsibility Principle (SRP)**: Keep components focused on one responsibility (`config.py`, `tools.py`, `models.py`, `runner.py`).
- **Open/Closed Principle (OCP)**: Design toolsets and models to be easily extensible without modifying runner logic.
- **Dependency Inversion Principle (DIP)**: Depend on abstractions (`BaseChatModel`, `BaseTool`), injecting concrete dependencies at the composition root.
- **Modular Packaging**: Organize new model providers or experiments into dedicated subpackages (e.g., `groq_agent/`).

### Environment & Security
- **Strict Secrets Protection**: Never hardcode API keys or credentials. Always load from `.env` via `python-dotenv`.
- **Git Hygiene**: Keep `.env` and `logs/` ignored in `.gitignore`.

### Platform Compatibility (Windows UTF-8)
- Always configure standard streams for UTF-8 at script startup:
  ```python
  if sys.platform == "win32":
      try:
          sys.stdout.reconfigure(encoding="utf-8")
          sys.stderr.reconfigure(encoding="utf-8")
      except Exception:
          pass
  ```

### Tool Definitions & Verification
- **Type Annotations & Docstrings**: Explicit type hints and clear docstrings on all tool functions.
- **Error Handling**: Graceful error handling in tools (e.g., division by zero).
- **Verification**: Test and verify execution in the terminal before reporting results.

---

## 5. Skill Orchestration Bridge & Decision Matrix

This bridge defines when and how the agent must activate specialized skills and orchestrate their combinations.

### Available Workspace Skills:
1. **[`senior-python-dev`](.agents/skills/senior-python-dev/SKILL.md)**: Modern Python 3.10+, protocols, async concurrency, strict typing, domain exceptions.
2. **[`senior-langchain-llm`](.agents/skills/senior-langchain-llm/SKILL.md)**: LangChain v0.3+, LangGraph, tool schema engineering, multi-provider resilience, fallbacks.
3. **[`architecture-design-patterns`](.agents/skills/architecture-design-patterns/SKILL.md)**: SOLID architecture, Hexagonal/Clean architecture, design patterns, and agentic workflows.
4. **[`git-conventions`](.agents/skills/git-conventions/SKILL.md)**: Modern production-ready Git branch naming and conventional commits.

### Skill Activation & Combination Matrix:

| Task Type | Primary Skill | Supporting Skill(s) | Required Output Standard |
| :--- | :--- | :--- | :--- |
| **Python Code Writing & Refactoring** | `senior-python-dev` | `architecture-design-patterns` | Strict typing (Protocols/Union syntax), custom exceptions, clean imports, zero magic values. |
| **LLM / Tool / Agent Development** | `senior-langchain-llm` | `senior-python-dev` | Bulletproof `@tool` docstrings, return string error handling, `init_chat_model` provider decoupling. |
| **New Project / Subsystem Design** | `architecture-design-patterns` | `senior-python-dev`, `senior-langchain-llm` | SOLID adherence, separated `config`/`tools`/`models`/`runner`/`main`, composition root. |
| **Full Agentic Pipeline (End-to-End)** | **All 3 Skills Combined** | — | Clean Architecture layers, resilient fallback LLMs, structured error trapping, Windows UTF-8 safety. |
| **Version Control & Commits** | `git-conventions` | — | Conventional commits (`feat`, `fix`, `chore`), detailed atomic bodies, and strict branch naming. |

### Execution Workflow:
1. **Analyze Requirements**: Determine which skill domain(s) apply to the user's prompt using the matrix above.
2. **Consult Skill Guidelines**: Apply the specific standards (e.g., design patterns from `architecture-design-patterns` + tool error handling from `senior-langchain-llm` + typing from `senior-python-dev`).
3. **Verify Execution**: Always execute scripts in the terminal to verify runtime behavior before presenting the solution to the user.

---

## 6. Custom Commands (Agent Triggers)

The user may invoke the following custom pseudo-commands in their prompts. When you see these commands, immediately execute the corresponding workflow without asking for permission:

- **`/branch-feat [feature-name]`**:
  1. Read the `[feature-name]` argument.
  2. Format it into kebab-case if it isn't already.
  3. Execute `git checkout -b feature/<feature-name>`.
  4. Confirm the branch creation to the user.

- **`/branch-bug [bug-name]`**:
  1. Execute `git checkout -b bugfix/<bug-name>`.
  2. Confirm the branch creation to the user.
