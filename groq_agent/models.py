"""Model provider module for Groq LLMs.

Adheres to Single Responsibility Principle (SRP) and Dependency Inversion Principle (DIP):
Encapsulates chat model creation returning standard BaseChatModel interface.
"""

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

# Recommended available Groq models (free tier):
# - "openai/gpt-oss-120b" (Fast, high capability reasoning)
# - "qwen/qwen3.8-27b"     (Strong generalist)
# - "openai/gpt-oss-20b"  (Lightweight & fast)
# - "qwen/qwen3.6-27b"
DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"


def get_groq_model(model_name: str = DEFAULT_GROQ_MODEL, **kwargs) -> BaseChatModel:
    """Initialize and return a Groq chat model via LangChain's init_chat_model.

    Args:
        model_name: Name of the model on Groq.
        **kwargs: Additional parameters passed to init_chat_model (e.g. temperature).

    Returns:
        BaseChatModel: Configured chat model instance.
    """
    model_identifier = f"groq:{model_name}" if not model_name.startswith("groq:") else model_name
    return init_chat_model(model_identifier, **kwargs)
