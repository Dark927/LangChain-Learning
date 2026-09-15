"""
Manages external LLM provider API keys and model definitions.
Supports Groq, Google Gemini, OpenAI-compatible, and Anthropic free-tier models.
Keys are stored securely in a separate keys.json file, never bundled or committed.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class ProviderModel:
    """Represents a single selectable LLM model from an external provider."""

    provider_id: str
    display_name: str
    model_id: str
    requires_key: str
    free_tier_note: str


class ProviderRegistry:
    """
    Central registry of all supported external LLM provider models.
    Free-tier models reset daily or weekly and act as smart fallbacks.
    """

    ALL_MODELS: ClassVar[list[ProviderModel]] = [
        ProviderModel(
            provider_id="groq",
            display_name="Groq — Llama 3.3 70B (Free)",
            model_id="llama-3.3-70b-versatile",
            requires_key="GROQ_API_KEY",
            free_tier_note="Free tier: ~14,400 req/day, resets daily",
        ),
        ProviderModel(
            provider_id="groq",
            display_name="Groq — Gemma 2 9B (Free)",
            model_id="gemma2-9b-it",
            requires_key="GROQ_API_KEY",
            free_tier_note="Free tier: ~14,400 req/day, resets daily",
        ),
        ProviderModel(
            provider_id="groq",
            display_name="Groq — Mistral Saba (Free)",
            model_id="mistral-saba-24b",
            requires_key="GROQ_API_KEY",
            free_tier_note="Free tier: ~14,400 req/day, resets daily",
        ),
        ProviderModel(
            provider_id="google_genai",
            display_name="Google — Gemini 2.0 Flash (Free)",
            model_id="gemini-2.0-flash",
            requires_key="GOOGLE_API_KEY",
            free_tier_note="Free tier: 1,500 req/day, resets daily",
        ),
        ProviderModel(
            provider_id="google_genai",
            display_name="Google — Gemini 2.5 Flash (Free)",
            model_id="gemini-2.5-flash",
            requires_key="GOOGLE_API_KEY",
            free_tier_note="Free tier: 500 req/day, resets daily",
        ),
        ProviderModel(
            provider_id="openai",
            display_name="OpenAI — GPT-4o Mini",
            model_id="gpt-4o-mini",
            requires_key="OPENAI_API_KEY",
            free_tier_note="Pay-as-you-go (very cheap)",
        ),
        ProviderModel(
            provider_id="anthropic",
            display_name="Anthropic — Claude Haiku 3.5",
            model_id="claude-haiku-4-5",
            requires_key="ANTHROPIC_API_KEY",
            free_tier_note="Pay-as-you-go (very cheap)",
        ),
    ]

    @classmethod
    def get_by_display_name(cls, name: str) -> ProviderModel | None:
        """Find a registered model by its UI display name."""
        return next((m for m in cls.ALL_MODELS if m.display_name == name), None)

    @classmethod
    def display_names(cls) -> list[str]:
        """Return all display names for populating UI dropdowns."""
        return [m.display_name for m in cls.ALL_MODELS]


def _get_keys_path() -> str:
    """Resolve the path to the secure keys.json file, works in both dev and frozen contexts."""
    base_dir = (
        os.path.dirname(sys.executable)
        if getattr(sys, "frozen", False)
        else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    return os.path.join(base_dir, "data", "api_keys.json")


def load_api_keys() -> dict[str, str]:
    """Load all stored API keys from disk. Returns empty dict if file doesn't exist."""
    path = _get_keys_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_api_keys(keys: dict[str, str]) -> None:
    """Persist API keys dict to disk, creating the data directory if needed."""
    path = _get_keys_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(keys, f, indent=4)


def get_key(key_name: str) -> str | None:
    """Retrieve a single API key by its name (e.g. 'GROQ_API_KEY')."""
    return load_api_keys().get(key_name)
