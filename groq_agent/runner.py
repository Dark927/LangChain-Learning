"""Agent runner and execution formatting module.

Adheres to Single Responsibility Principle (SRP) and Dependency Inversion Principle (DIP):
Takes model and tool abstractions as dependencies to create and run agent instances.
"""

from typing import Sequence, Any
from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from .config import get_logger


def extract_text(content: Any) -> str:
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


class GroqAgentRunner:
    """Orchestrates creation, execution, logging, and display of an agent."""

    def __init__(self, model: BaseChatModel, tools: Sequence[BaseTool]):
        self.model = model
        self.tools = list(tools)
        self.agent = create_agent(model=self.model, tools=self.tools)
        self.logger = get_logger()

    def run(self, messages: list[tuple[str, str]]) -> dict[str, Any]:
        """Execute the agent on a list of input messages and print formatted trace."""
        self.logger.info(f"--- Starting Agent Execution with input: {messages} ---")
        print("-" * 60)

        result = self.agent.invoke({"messages": messages})

        for message in result["messages"]:
            # Log complete message details to log file
            raw_info = {
                "type": message.type,
                "content": message.content,
                "additional_kwargs": getattr(message, "additional_kwargs", {}),
                "response_metadata": getattr(message, "response_metadata", {}),
                "tool_calls": getattr(message, "tool_calls", None),
            }
            self.logger.info(f"Raw message: {raw_info}")

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
        self.logger.info("--- Agent Execution Completed ---")
        return result
