"""Agent Runner module.

Purpose:
This file combines the AI model and the tools together into an "Agent".
It then runs the Agent and handles printing the conversation nicely to the screen.
"""

from typing import Any
from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool

# We import the logger we set up in config.py
from .config import get_agent_logger

# --- CONSTANTS ---
DIVIDER_LINE = "-" * 60

# These are the different types of messages the AI system uses internally.
ROLE_HUMAN = "human"
ROLE_AI = "ai"
ROLE_TOOL = "tool"
ROLE_ERROR = "error"


def get_text_from_message(content: Any) -> str:
    """Extracts plain text from the AI's complex message formats.
    
    Logic & Purpose:
    Sometimes the AI returns a simple string: "Hello!".
    Sometimes it returns a complex list of dictionaries if it includes images or special data.
    This function looks at the data and pulls out just the readable text so we can print it.
    """
    # If it's already a simple text string, just return it.
    if isinstance(content, str):
        return content

    # If it's a list (complex format), look through each item and find the text.
    if isinstance(content, list):
        extracted_pieces = []
        for item in content:
            if isinstance(item, str):
                extracted_pieces.append(item)
            elif isinstance(item, dict) and "text" in item:
                extracted_pieces.append(str(item["text"]))
        return "".join(extracted_pieces)

    # If it's something else, force it to be a string.
    if content is None:
        return ""
    return str(content)


class AgentRunner:
    """This class runs the AI agent and manages the conversation history."""

    def __init__(self, model: BaseChatModel, tools: list[BaseTool]) -> None:
        """Sets up the Agent Runner.
        
        Logic & Purpose:
        LangChain's 'create_agent' function binds the model and tools together.
        When the agent runs, it knows it can use these specific tools.
        """
        self.model = model
        self.tools = tools
        self.agent = create_agent(model=self.model, tools=self.tools)
        self.logger = get_agent_logger()

    def execute_conversation(self, messages: list[tuple[str, str]]) -> dict[str, Any]:
        """Sends the user's message to the AI and prints every step it takes.
        
        Args:
            messages: A list of messages, like [("user", "What is 2 * 2?")]
            
        Returns:
            The complete result dictionary containing the whole conversation history.
        """
        self.logger.info(f"--- Starting conversation with input: {messages} ---")
        print(DIVIDER_LINE)

        # 1. Ask the agent to think and respond!
        # The agent will think, use tools if it needs to, and eventually give a final answer.
        result = self.agent.invoke({"messages": messages})

        # 2. Print out the history of what just happened.
        # result["messages"] contains every step (User asking -> AI thinking -> Tool running -> AI answering)
        for message in result["messages"]:
            
            # Save the raw data to our log file so we can debug it later if needed.
            self.logger.info(f"Message step: {message.type} - {message.content}")

            # Did the user say this?
            if message.type == ROLE_HUMAN:
                user_text = get_text_from_message(message.content)
                print(f"User: {user_text}")

            # Did the AI say this?
            elif message.type == ROLE_AI:
                ai_text = get_text_from_message(message.content).strip()
                if ai_text:
                    print(f"AI: {ai_text}")

                # If the AI decided to use a tool, it is stored in 'tool_calls'
                tool_calls = getattr(message, "tool_calls", None)
                if tool_calls:
                    for call in tool_calls:
                        print(f"Tool Call: {call['name']} | Input: {call['args']}")

            # Is this the result returned by a tool?
            elif message.type == ROLE_TOOL:
                tool_output = get_text_from_message(message.content)
                print(f"Tool Result: {message.name} | Output: {tool_output}")

            # Did something break?
            elif message.type == ROLE_ERROR:
                print(f"Error: {message.content}")

        print(DIVIDER_LINE)
        self.logger.info("--- Conversation Completed ---")
        
        return result
