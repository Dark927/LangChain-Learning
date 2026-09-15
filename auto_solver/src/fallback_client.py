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


def _build_model(model_def: ProviderModel) -> BaseChatModel | None:
    """
    Construct a LangChain BaseChatModel for a given provider model definition.
    Injects the API key into environment before initialization.

    Args:
        model_def: The ProviderModel descriptor from the registry.

    Returns:
        A ready-to-invoke BaseChatModel, or None if the key is missing.
    """
    key_value = get_key(model_def.requires_key)
    if not key_value:
        return None

    # Inject key into environment so LangChain providers can pick it up
    os.environ[model_def.requires_key] = key_value

    try:
        return init_chat_model(
            model=model_def.model_id,
            model_provider=model_def.provider_id,
        )
    except Exception as e:
        print(f"[Fallback] Failed to build model '{model_def.display_name}': {e}")
        return None


def build_fallback_chain(selected_display_name: str | None) -> BaseChatModel | None:
    """
    Build a resilient LangChain model chain.
    The user-selected model is the primary. All remaining configured models are chained
    as automatic fallbacks using LangChain's .with_fallbacks().

    Args:
        selected_display_name: The UI display name of the user's selected primary model.

    Returns:
        A resilient BaseChatModel chain, or None if no keys are configured at all.
    """
    primary_def = ProviderRegistry.get_by_display_name(selected_display_name or "")
    all_models_with_keys: list[BaseChatModel] = []

    # Build primary first if selected and has a key
    primary_model: BaseChatModel | None = None
    if primary_def:
        primary_model = _build_model(primary_def)

    # Build all other configured models as fallbacks
    fallbacks: list[BaseChatModel] = []
    for model_def in ProviderRegistry.ALL_MODELS:
        if primary_def and model_def.display_name == primary_def.display_name:
            continue
        built = _build_model(model_def)
        if built:
            fallbacks.append(built)

    if primary_model is None and not fallbacks:
        return None

    if primary_model is None:
        primary_model = fallbacks.pop(0)

    if fallbacks:
        return primary_model.with_fallbacks(fallbacks)

    return primary_model


def ask_fallback(
    prompt: str,
    selected_model_name: str | None,
    live_log_callback: Callable[[str], None] | None = None,
) -> str:
    """
    Send a prompt to the configured fallback LLM chain and return the answer.
    Gracefully returns an empty string on any failure.

    Args:
        prompt: The full question prompt to send.
        selected_model_name: Display name of the user-selected primary fallback model.
        live_log_callback: Optional callback to stream status messages to the UI log.

    Returns:
        The model's text response, or empty string on any failure.
    """
    chain = build_fallback_chain(selected_model_name)
    if chain is None:
        if live_log_callback:
            live_log_callback("[Fallback] No API keys configured. Skipping fallback models.")
        return ""

    trimmed_prompt = prompt[:_FALLBACK_MAX_CHARS]

    try:
        if live_log_callback:
            live_log_callback(f"[Fallback] Querying external LLM...")
        response = chain.invoke([HumanMessage(content=trimmed_prompt)])
        text = response.content if hasattr(response, "content") else str(response)
        if live_log_callback:
            live_log_callback(f"[Fallback] Got response.")
        return text.strip()
    except Exception as e:
        if live_log_callback:
            live_log_callback(f"[Fallback] All models failed: {e}")
        return ""
