"""Model setup module.

Purpose:
This file is responsible for connecting to the Groq AI service.
It returns an "AI Model" object that we can use to talk to the AI.
"""

from typing import Any
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

# --- CONSTANTS ---
# Groq provides several free models. We specify a highly capable one here.
DEFAULT_MODEL_NAME = "openai/gpt-oss-120b"

# We must prefix the model name with "groq:" so LangChain knows which company's API to call.
PROVIDER_PREFIX = "groq:"


def create_ai_model(model_name: str = DEFAULT_MODEL_NAME, **config: Any) -> BaseChatModel:
    """Connects to Groq and creates a Chat Model object.
    
    Logic & Purpose:
    LangChain's 'init_chat_model' is a factory function. It takes a string like 
    "groq:openai/gpt-oss-120b" and automatically sets up the correct connection 
    using the API key we loaded in config.py.
    
    Args:
        model_name: The name of the AI model to use.
        **config: Extra settings (like temperature, which controls creativity).
        
    Returns:
        BaseChatModel: A ready-to-use AI model object.
    """
    # If the user didn't type "groq:" at the start of the name, we add it for them.
    if not model_name.startswith(PROVIDER_PREFIX):
        full_model_name = f"{PROVIDER_PREFIX}{model_name}"
    else:
        full_model_name = model_name
        
    # Create and return the model
    return init_chat_model(full_model_name, **config)
