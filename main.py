import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows terminal (avoids UnicodeEncodeError for characters like ⅔)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

script_dir = Path(__file__).resolve().parent
env_path = script_dir / ".env"

# -------------------
# Logs Setup
# -------------------
logs_dir = script_dir / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)

log_file = logs_dir / "agent.log"
logging.basicConfig(
    filename=str(log_file),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8",
)

print("Script directory: ", script_dir)
print("Using .env from: ", env_path)

load_dotenv(dotenv_path=env_path)

print("Google AI API key found: ", bool(os.getenv("GOOGLE_API_KEY")))

# -------------------
# Model
# -------------------

from langchain.chat_models import init_chat_model

model = init_chat_model("google_genai:gemini-3.5-flash-lite")

# -------------------
# Tools
# -------------------

from langchain_core.tools import tool


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


# -------------------
# Agents
# -------------------

from langchain.agents import create_agent

tools = [multiply, divide]

agent = create_agent(model=model, tools=tools)

print("-" * 60)


def extract_text(content) -> str:
    """Extract clean string text from string or structured content blocks."""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, str):
                text_parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                text_parts.append(item["text"])
            elif hasattr(item, "text"):
                text_parts.append(getattr(item, "text"))
        return "".join(text_parts)
    return str(content) if content is not None else ""


def run_agent(agent, messages):
    logging.info(f"--- Starting Agent Execution with input: {messages} ---")
    result = agent.invoke({"messages": messages})

    for message in result["messages"]:
        # Log complete message details to log file
        raw_info = {
            "type": message.type,
            "content": message.content,
            "additional_kwargs": getattr(message, "additional_kwargs", {}),
            "response_metadata": getattr(message, "response_metadata", {}),
            "tool_calls": getattr(message, "tool_calls", None),
        }
        logging.info(f"Raw message: {raw_info}")

        # Human/User messages
        if message.type == "human":
            user_text = extract_text(message.content)
            print(f"User: {user_text}")

        # AI messages contain standard text AND/OR the requested tool inputs
        elif message.type == "ai":
            clean_text = extract_text(message.content).strip()
            if clean_text:
                print(f"AI: {clean_text}")

            if getattr(message, "tool_calls", None):
                for call in message.tool_calls:
                    print(f"Tool Call: {call['name']} | Input: {call['args']}")

        # Tool messages contain ONLY the output/result of the tool
        elif message.type == "tool":
            tool_output = extract_text(message.content)
            print(f"Tool Result: {message.name} | Output: {tool_output}")

        elif message.type == "error":
            print(f"Error: {message.content}")

    print("-" * 60)
    logging.info("--- Agent Execution Completed ---")
    return result


run_agent(agent, [("user", "What is 145 multiplied by 8, then divided by 3?")])
