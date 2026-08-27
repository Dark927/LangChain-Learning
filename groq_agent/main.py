"""Main Entry Point for the Groq Agent.

Purpose:
This file brings all the separate pieces together: Configuration, Tools, Model, and Runner.
This pattern is called "Dependency Injection" - we create the parts separately and plug them into the Runner.
"""

import sys
from pathlib import Path

# This block allows us to run this script directly by telling Python where the other files are.
current_dir = Path(__file__).resolve().parent
project_dir = current_dir.parent
sys.path.insert(0, str(project_dir))

# Import our customized modules
from groq_agent.config import prepare_environment
from groq_agent.models import create_ai_model
from groq_agent.tools import MATH_TOOLS
from groq_agent.runner import AgentRunner

# --- CONSTANTS ---
ROLE_USER = "user"
EXAMPLE_QUESTION = "What is 145 multiplied by 8, then divided by 3?"


def main() -> None:
    """The main function that starts our application."""
    
    # Step 1: Prepare the environment (logs, API keys, Windows console fixes)
    prepare_environment()

    # Step 2: Create the AI model connection (Using our default Groq model)
    model = create_ai_model()
    
    # Step 3: Get our list of tools (Multiply and Divide)
    tools = MATH_TOOLS

    # Step 4: Plug the model and tools into our Runner
    runner = AgentRunner(model=model, tools=tools)

    # Step 5: Ask the AI a question!
    # We pass it as a list of tuples: [("role", "message text")]
    print("\nStarting the AI Agent...")
    runner.execute_conversation([(ROLE_USER, EXAMPLE_QUESTION)])


# This checks if the file is being run directly (like 'python main.py')
if __name__ == "__main__":
    main()
