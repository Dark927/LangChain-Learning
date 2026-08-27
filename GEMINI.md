# Project Rules for Agentic AI Workspace

These rules govern the development, coding standards, and agent behavior within this workspace.

---

## 1. Architecture & SOLID Design Principles
- **Single Responsibility Principle (SRP)**: Keep components focused on one responsibility.
  - Configuration & Environment: in `config.py`
  - Tool definitions & registries: in `tools.py`
  - Model providers & factories: in `models.py`
  - Execution, logging, & output formatting: in `runner.py`
- **Open/Closed Principle (OCP)**: Design toolsets and models to be easily extensible without modifying existing runner logic.
- **Dependency Inversion Principle (DIP)**: High-level orchestrators must depend on abstractions (`BaseChatModel`, `BaseTool`), with concrete dependencies injected at the composition root.
- **Modular Packaging**: When adding support for new model providers or experiments, organize them in dedicated subpackages (e.g., `groq_agent/`) rather than creating monolithic single-file scripts.

---

## 2. Safety & Code Preservation
- **Preserve Existing Code**: Do not modify or overwrite existing working scripts (such as `main.py`) unless explicitly instructed by the user.
- **Incremental Additions**: For new features, providers, or alternative approaches, create new modules or subdirectories.

---

## 3. Environment & Security
- **Strict Secrets Protection**: Never hardcode API keys or credentials in source files. Always load from `.env` via `python-dotenv`.
- **Git Hygiene**: Keep `.env` and `logs/` ignored in `.gitignore`. Provide clean examples in `.env.example`.

---

## 4. Platform Compatibility (Windows UTF-8)
- **Windows Terminal Output**: Always configure standard output / error streams for UTF-8 at script start to prevent `UnicodeEncodeError` (e.g., math symbols, emoji, fractions):
  ```python
  if sys.platform == "win32":
      try:
          sys.stdout.reconfigure(encoding="utf-8")
          sys.stderr.reconfigure(encoding="utf-8")
      except Exception:
          pass
  ```

---

## 5. Agent Tools & Type Hinting
- **Type Annotations**: Provide explicit type hints for all tool functions, arguments, and return types.
- **Tool Docstrings**: Every tool function decorated with `@tool` must have a clear, concise docstring explaining what it does, its arguments, and its expected outputs (this is essential for LLM tool calling accuracy).
- **Error Handling**: Tools must handle edge cases gracefully (e.g., division by zero) and return informative error messages rather than raising unhandled exceptions.

---

## 6. Execution & Verification
- **Test Before Reporting**: Whenever scripts or agents are modified or created, verify execution in the terminal to ensure tool calling, parsing, and outputs function end-to-end.
- **Structured Logging**: Log all raw model responses, tool calls, and execution steps to the `logs/` directory for debugging and learning inspection.
