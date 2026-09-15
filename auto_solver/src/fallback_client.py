"""
Fallback LLM client that wraps external provider models (Groq, Google, OpenAI, Anthropic).
Used automatically when Antigravity CLI fails or returns no answer.
Leverages LangChain's unified init_chat_model with .with_fallbacks() for multi-provider resilience.
"""
from __future__ import annotations

import os
from typing import Callable

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage

from provider_registry import ProviderModel, ProviderRegistry, get_key

# Maximum characters sent to the fallback model to avoid burning tokens
_FALLBACK_MAX_CHARS: int = 3000


def _build_model(model_def: ProviderModel) -> tuple[ProviderModel, BaseChatModel] | None:
    """
    Construct a LangChain BaseChatModel for a given provider model definition.
    Injects the API key into environment before initialization.

    Args:
        model_def: The ProviderModel descriptor from the registry.

    Returns:
        Tuple of (ProviderModel, BaseChatModel), or None if the key is missing.
    """
    key_value = get_key(model_def.requires_key)
    if not key_value:
        return None

    # Inject key into environment so LangChain providers can pick it up
    os.environ[model_def.requires_key] = key_value

    try:
        if model_def.provider_id == "openrouter":
            from langchain_openrouter import ChatOpenRouter
            model = ChatOpenRouter(
                model=model_def.model_id,
                api_key=key_value,
            )
        else:
            model = init_chat_model(
                model=model_def.model_id,
                model_provider=model_def.provider_id,
            )
        return (model_def, model)
    except Exception as e:
        print(f"[Fallback] Failed to build model '{model_def.display_name}': {e}")
        return None


def get_configured_fallback_models(selected_display_name: str | None) -> list[tuple[ProviderModel, BaseChatModel]]:
    """
    Build a list of all configured fallback models.
    The user-selected model is placed first. All remaining configured models follow.
    """
    primary_def = ProviderRegistry.get_by_display_name(selected_display_name or "")
    models: list[tuple[ProviderModel, BaseChatModel]] = []

    # Build primary first if selected and has a key
    if primary_def:
        built = _build_model(primary_def)
        if built:
            models.append(built)

    # Build all other configured models as fallbacks
    for model_def in ProviderRegistry.ALL_MODELS:
        if primary_def and model_def.display_name == primary_def.display_name:
            continue
        built = _build_model(model_def)
        if built:
            models.append(built)

    return models


def ask_fallback(
    prompt: str,
    selected_model_name: str | None,
    live_log_callback: Callable[[str], None] | None = None,
) -> str:
    """
    Send a prompt to the fallback LLMs. Automatically switches to the next available model if one fails.
    """
    models = get_configured_fallback_models(selected_model_name)
    if not models:
        if live_log_callback:
            live_log_callback("[Fallback] No API keys configured. Skipping fallback models.")
        return ""

    trimmed_prompt = prompt[:_FALLBACK_MAX_CHARS]
    
    for i, (model_def, model_client) in enumerate(models):
        try:
            if live_log_callback:
                prefix = "Primary Fallback" if i == 0 else f"Auto-Switching to Fallback {i+1}"
                # Extract clean name like "Llama 3.3 70B" from "Groq — Llama 3.3 70B (Free)"
                clean_name = model_def.display_name.split("—")[-1].replace("(Free)", "").strip()
                live_log_callback(f"[Fallback] {prefix}: {clean_name}...")
                
            response = model_client.invoke([HumanMessage(content=trimmed_prompt)])
            text = response.content if hasattr(response, "content") else str(response)
            
            if isinstance(text, list):
                # Google Gemini sometimes returns a list of parts
                parts = []
                for part in text:
                    if isinstance(part, dict) and "text" in part:
                        parts.append(part["text"])
                    elif isinstance(part, str):
                        parts.append(part)
                    else:
                        parts.append(str(part))
                text = " ".join(parts)
                
            if not isinstance(text, str):
                text = str(text)

            if live_log_callback:
                live_log_callback(f"[Fallback] Success!")
            return text.strip()
            
        except Exception as e:
            if live_log_callback:
                err_msg = str(e).split('\n')[0][:50]
                live_log_callback(f"[Fallback] {model_def.provider_id} failed ({err_msg})...")
            continue

    if live_log_callback:
        live_log_callback(f"[Fallback] All configured models failed.")
    return ""
