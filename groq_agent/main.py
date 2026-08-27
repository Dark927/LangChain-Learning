"""Main entrypoint for Groq Agent.

Adheres to Dependency Injection / Composition Root:
Wires together configuration, model provider, tool set, and runner.
"""

import sys
from pathlib import Path

# Support running directly (`python groq_agent/main.py`) or as module (`python -m groq_agent.main`)
if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from groq_agent.config import setup_environment
    from groq_agent.models import get_groq_model
    from groq_agent.tools import MATH_TOOLS
    from groq_agent.runner import GroqAgentRunner
else:
    from .config import setup_environment
    from .models import get_groq_model
    from .tools import MATH_TOOLS
    from .runner import GroqAgentRunner


def main() -> None:
    # 1. Setup environment, encoding, and logging
    setup_environment()

    # 2. Dependency Injection: Instantiate model & tools
    model = get_groq_model()
    tools = MATH_TOOLS

    # 3. Create runner with injected dependencies
    runner = GroqAgentRunner(model=model, tools=tools)

    # 4. Run sample query
    query = "What is 145 multiplied by 8, then divided by 3?"
    runner.run([("user", query)])


if __name__ == "__main__":
    main()
