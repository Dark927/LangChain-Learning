---
name: senior-python-dev
description: >-
  Expert guidelines and best practices for modern Python engineering.
  Use when designing, writing, refactoring, or reviewing Python code, enforcing strict typing,
  asynchronous programming, performance optimization, and robust error handling.
---

# Senior Python Developer Skill

Comprehensive engineering guide for writing production-grade, maintainable, and type-safe Python systems (Python 3.10+).

---

## 1. Advanced Type Hinting & Type Safety

Always use modern, expressive type annotations (`typing` and `collections.abc`):

- **Protocols (Structural Subtyping / Duck Typing)**: Prefer `typing.Protocol` over rigid inheritance for interfaces.
  ```python
  from typing import Protocol, runtime_checkable

  @runtime_checkable
  class Formattable(Protocol):
      def format(self) -> str: ...
  ```
- **Union Syntax**: Use PEP 604 pipe syntax (`str | int | None` instead of `Optional[Union[str, int]]`).
- **Generics & TypeVar**: Use `TypeVar`, `Generic`, and `ParamSpec` for reusable, type-safe utilities and decorators.
- **TypedDict & Dataclasses**:
  - Use `@dataclass(slots=True, frozen=True)` for immutable domain models.
  - Use `TypedDict` for external API JSON shapes where class instantiation overhead is undesirable.
  - Use Pydantic `BaseModel` when input validation and serialization are required.

---

## 2. Robust Error Handling & Defensive Programming

- **Custom Domain Exceptions**: Derive domain-specific exceptions from a common base exception class:
  ```python
  class AppError(Exception):
      """Base exception for the application."""

  class ConfigurationError(AppError):
      """Raised when environment or configuration is invalid."""

  class ToolExecutionError(AppError):
      """Raised when a tool fails to execute safely."""
  ```
- **Context Managers**: Wrap resources (files, sockets, database sessions) in context managers (`with` / `async with` or `@contextmanager`).
- **Explicit Failure Modes**: Do not silence exceptions with bare `except: pass`. Handle specific exception types and preserve traceback with `raise ... from exc`.

---

## 3. Asynchronous Programming & Concurrency

- **Structured Concurrency**: Use `asyncio.TaskGroup` (Python 3.11+) over unshielded `asyncio.gather` to ensure task cancellation safety.
- **Non-blocking I/O**: Ensure all network calls and file operations in async paths use async libraries (`aiohttp`, `httpx`, `aiofiles`) or are delegated to thread pools (`asyncio.to_thread`).
- **Thread Safety**: Never mutate shared state across threads without locks or thread-safe queues (`asyncio.Queue`, `queue.Queue`).

---

## 4. Platform & Environment Compatibility

- **Windows Stream Encoding**: Always ensure stdout/stderr are UTF-8 configured:
  ```python
  import sys
  if sys.platform == "win32":
      try:
          sys.stdout.reconfigure(encoding="utf-8")
          sys.stderr.reconfigure(encoding="utf-8")
      except Exception:
          pass
  ```
- **Pathlib**: Always use `pathlib.Path` for cross-platform filesystem operations. Never use raw string concatenation for paths.
- **Secrets & Dotenv**: Strictly load environment secrets via `dotenv.load_dotenv()` into `os.getenv()`. Never commit secrets.

---

## 5. Code Quality & Verification Standards

1. **Pure Functions & Immutability**: Minimize side effects; prefer returning new data structures over in-place mutation.
2. **Imports Organization**: Standard library first, followed by third-party packages, followed by local imports.
3. **Execution Verification**: Always execute Python modules in the terminal to verify syntax, runtime behavior, and typing before declaring completion.
