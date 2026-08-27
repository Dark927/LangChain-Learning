"""Tools module.

Purpose:
This file defines the "actions" or "tools" the AI is allowed to use.
The AI cannot do math on its own reliably, so we give it Python functions (tools) to do the math for it.
"""

from langchain_core.tools import tool, BaseTool

# --- CONSTANTS ---
ZERO = 0
ERROR_DIVIDE_BY_ZERO = "Error: You cannot divide by zero!"


# The @tool decorator tells the LangChain framework that this function is an AI tool.
# LangChain reads the docstring below ("Multiply two numbers together...") and sends it to the AI.
# This is how the AI knows WHAT the tool does and WHEN to use it.
@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers together.
    
    Use this tool whenever you need to compute the product of two numeric values.
    
    Args:
        a: The first number.
        b: The second number.
        
    Returns:
        float: The result of multiplying a and b.
    """
    return a * b


@tool
def divide(a: float, b: float) -> float | str:
    """Divide the first number by the second number.
    
    Use this tool whenever you need to perform division.
    
    Args:
        a: The dividend (the number being divided).
        b: The divisor (the number dividing by).
        
    Returns:
        float | str: The result of the division, or an error message if b is zero.
    """
    # Logic & Purpose:
    # If a program divides by zero, it normally crashes. 
    # Instead of crashing, we return a text error message to the AI.
    # The AI reads the error message and can try a different approach or apologize to the user.
    if b == ZERO:
        return ERROR_DIVIDE_BY_ZERO
        
    return a / b


# We bundle our tools into a single list so we can easily give them to the agent later.
MATH_TOOLS: list[BaseTool] = [multiply, divide]
