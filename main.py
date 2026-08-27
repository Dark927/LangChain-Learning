"""Google AI (Gemini) Agent - Unified File.

Purpose:
This is a self-contained, beginner-friendly script that builds an AI agent using Google Gemini.
It includes configuration, tools, model setup, and the running loop all in one file for easy learning.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain_core.tools import tool

# --- CONSTANTS ---
# We use constants to avoid "magic numbers" and "magic strings" in our code.
UTF8 = "utf-8"
WINDOWS_OS = "win32"
ENV_FILE = ".env"
LOG_FOLDER = "logs"
LOG_FILE = "agent_google.log"

API_KEY_VAR = "GOOGLE_API_KEY"
GEMINI_MODEL = "google_genai:gemini-3.5-flash-lite"
# To use the Pro model, you would change the line above to:
# GEMINI_MODEL = "google_genai:gemini-3.1-pro-preview"

ZERO = 0
ERROR_DIVIDE_BY_ZERO = "Error: Cannot divide by zero!"
DIVIDER = "-" * 60

ROLE_USER = "user"
EXAMPLE_QUESTION = "What is 145 multiplied by 8, then divided by 3?"


# ==========================================
# 1. ENVIRONMENT & LOGGING SETUP
# ==========================================

# Fix Windows console to support math symbols and special characters
if sys.platform == WINDOWS_OS:
    try:
        sys.stdout.reconfigure(encoding=UTF8)
        sys.stderr.reconfigure(encoding=UTF8)
    except Exception:
        pass

# Find our folders automatically
script_dir = Path(__file__).resolve().parent
env_path = script_dir / ENV_FILE
logs_dir = script_dir / LOG_FOLDER
logs_dir.mkdir(parents=True, exist_ok=True)

# Set up logging to a file
logging.basicConfig(
    filename=str(logs_dir / LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding=UTF8,
)

# Load secret API keys from the .env file
load_dotenv(dotenv_path=env_path)
print(f"Google AI API key loaded: {bool(os.getenv(API_KEY_VAR))}")


# ==========================================
# 2. TOOL DEFINITIONS
# ==========================================

@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers together. Use this when you need to find a product."""
    return a * b


@tool
def divide(a: float, b: float) -> float | str:
    """Divide the first number by the second.
    
    Logic & Purpose:
    Returns a string error instead of crashing if the divisor is 0,
    so the AI can read the error and try something else.
    """
    if b == ZERO:
        return ERROR_DIVIDE_BY_ZERO
    return a / b


# Bundle tools into a list
my_tools = [multiply, divide]


# ==========================================
# 3. MODEL & AGENT CREATION
# ==========================================

# Connect to Google Gemini using LangChain's factory function
model = init_chat_model(GEMINI_MODEL)

# Bind the model and tools together into an Agent
agent = create_agent(model=model, tools=my_tools)


# ==========================================
# 4. RUNNER LOGIC
# ==========================================

def get_text(content: Any) -> str:
    """Extracts plain text from the AI's complex message responses."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # Join pieces of text if the response is a complex list of blocks
        return "".join(
            str(item["text"]) if isinstance(item, dict) and "text" in item else
            str(item) if isinstance(item, str) else ""
            for item in content
        )
    return str(content) if content is not None else ""


def run_agent(agent_obj: Any, question: str) -> None:
    """Sends the question to the AI and prints the conversation steps."""
    messages = [(ROLE_USER, question)]
    print(DIVIDER)
    
    # Run the AI!
    result = agent_obj.invoke({"messages": messages})

    # Loop through the history and print what happened
    for msg in result["messages"]:
        logging.info(f"Step: {msg.type} - {msg.content}")

        if msg.type == "human":
            print(f"User: {get_text(msg.content)}")

        elif msg.type == "ai":
            text = get_text(msg.content).strip()
            if text:
                print(f"AI: {text}")
            
            # Print tools the AI decided to use
            tool_calls = getattr(msg, "tool_calls", None)
            if tool_calls:
                for call in tool_calls:
                    print(f"Tool Call: {call['name']} | Input: {call['args']}")

        elif msg.type == "tool":
            print(f"Tool Result: {msg.name} | Output: {get_text(msg.content)}")

        elif msg.type == "error":
            print(f"Error: {msg.content}")

    print(DIVIDER)


# ==========================================
# 5. EXECUTION
# ==========================================
if __name__ == "__main__":
    print("\nStarting Google Gemini Agent...")
    run_agent(agent, EXAMPLE_QUESTION)
