"""Tools module for agent capabilities.

Adheres to Single Responsibility Principle (SRP) and Open/Closed Principle (OCP):
Tools are isolated, modular, and can be extended without modifying core orchestration logic.
"""

from langchain_core.tools import tool, BaseTool


@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers together. Use for multiplication operations."""
    return a * b


@tool
def divide(a: float, b: float) -> float:
    """Divide the first number by the second. Returns error if dividing by zero."""
    if b == 0:
        return "Error: Cannot divide by zero!"
    return a / b


# Default list of math tools conforming to List[BaseTool]
MATH_TOOLS: list[BaseTool] = [multiply, divide]
