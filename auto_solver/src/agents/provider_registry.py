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
    free_tier_note: str = ""
    is_free: bool = True

DYNAMIC_MODELS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "dynamic_models.json")


class ProviderRegistry:
    """
    Central registry of all supported external LLM provider models.
    """

    ALL_MODELS: ClassVar[list[ProviderModel]] = [
        # ── Groq (free tier, resets daily) ──────────────────────────────────
        ProviderModel(
            provider_id="groq",
            display_name="Groq — Llama 3.3 70B",
            model_id="llama-3.3-70b-versatile",
            requires_key="GROQ_API_KEY",
            free_tier_note="Free tier: ~14,400 req/day, resets daily",
            is_free=True,
        ),
        ProviderModel(
            provider_id="groq",
            display_name="Groq — Llama 3.1 8B",
            model_id="llama-3.1-8b-instant",
            requires_key="GROQ_API_KEY",
            free_tier_note="Free tier: fastest Groq model, resets daily",
            is_free=True,
        ),
        ProviderModel(
            provider_id="groq",
            display_name="Groq — Gemma 2 9B",
            model_id="gemma2-9b-it",
            requires_key="GROQ_API_KEY",
            free_tier_note="Free tier: ~14,400 req/day, resets daily",
            is_free=True,
        ),
        ProviderModel(
            provider_id="groq",
            display_name="Groq — Mistral Saba",
            model_id="mistral-saba-24b",
            requires_key="GROQ_API_KEY",
            free_tier_note="Free tier: ~14,400 req/day, resets daily",
            is_free=True,
        ),
        ProviderModel(
            provider_id="groq",
            display_name="Groq — DeepSeek R1 70B",
            model_id="deepseek-r1-distill-llama-70b",
            requires_key="GROQ_API_KEY",
            free_tier_note="Free tier: reasoning model, resets daily",
            is_free=True,
        ),
        # ── Google AI Studio (free tier, resets daily) ───────────────────────
        ProviderModel(
            provider_id="google_genai",
            display_name="Google — Gemini 3.5 Flash",
            model_id="gemini-3.5-flash",
            requires_key="GOOGLE_API_KEY",
            free_tier_note="Free tier: 1,500 req/day, resets daily",
            is_free=True,
        ),
        ProviderModel(
            provider_id="google_genai",
            display_name="Google — Gemini 3.7 Flash",
            model_id="gemini-3.7-flash",
            requires_key="GOOGLE_API_KEY",
            free_tier_note="Free tier: 500 req/day, resets daily",
            is_free=True,
        ),
        ProviderModel(
            provider_id="google_genai",
            display_name="Google — Gemini 3.5 Flash Lite",
            model_id="gemini-3.5-flash-lite",
            requires_key="GOOGLE_API_KEY",
            free_tier_note="Free tier: 1,500 req/day, fastest Google model",
            is_free=True,
        ),
        # ── OpenRouter (Free Tier) ──────────────────────────────────────────
        ProviderModel(
            provider_id="openrouter",
            display_name="OpenRouter — Gemma 4 26B (Free)",
            model_id="google/gemma-4-26b-a4b-it:free",
            requires_key="OPENROUTER_API_KEY",
            free_tier_note="Free models on OpenRouter, rate limits apply",
            is_free=True,
        ),
        ProviderModel(
            provider_id="openrouter",
            display_name="OpenRouter — Nemotron 3 120B (Free)",
            model_id="nvidia/nemotron-3-super-120b-a12b:free",
            requires_key="OPENROUTER_API_KEY",
            free_tier_note="Free models on OpenRouter, rate limits apply",
            is_free=True,
        ),
        
        # ====================================================================
        # ── PAID MODELS ─────────────────────────────────────────────────────
        # ====================================================================
        
        ProviderModel(
            provider_id="openai",
            display_name="OpenAI — GPT-4o Mini",
            model_id="gpt-4o-mini",
            requires_key="OPENAI_API_KEY",
            free_tier_note="Pay-as-you-go (very cheap)",
            is_free=False,
        ),
        ProviderModel(
            provider_id="openai",
            display_name="OpenAI — GPT-4.1 Nano",
            model_id="gpt-4.1-nano",
            requires_key="OPENAI_API_KEY",
            free_tier_note="Pay-as-you-go (cheapest OpenAI model)",
            is_free=False,
        ),
        ProviderModel(
            provider_id="anthropic",
            display_name="Anthropic — Claude Haiku 3.5",
            model_id="claude-haiku-4-5",
            requires_key="ANTHROPIC_API_KEY",
            free_tier_note="Pay-as-you-go (very cheap)",
            is_free=False,
        ),
        ProviderModel(
            provider_id="openrouter",
            display_name="OpenRouter — Claude 5 Sonnet (Paid)",
            model_id="anthropic/claude-sonnet-5",
            requires_key="OPENROUTER_API_KEY",
            free_tier_note="Pay-as-you-go OpenRouter routing",
            is_free=False,
        ),
    ]

    @classmethod
    def get_free_models(cls) -> list[str]:
        return [m.display_name for m in cls.ALL_MODELS if m.is_free]

    @classmethod
    def get_paid_models(cls) -> list[str]:
        return [m.display_name for m in cls.ALL_MODELS if not m.is_free]

    @classmethod
    def get_by_display_name(cls, name: str) -> ProviderModel | None:
        """Find a registered model by its UI display name."""
        return next((m for m in cls.ALL_MODELS if m.display_name == name), None)

    @classmethod
    def display_names(cls) -> list[str]:
        """Return all display names for populating UI dropdowns."""
        return [m.display_name for m in cls.ALL_MODELS]

    @classmethod
    def update_dynamic_models(cls) -> int:
        """Fetch models from connected APIs and save them to disk."""
        import requests
        
        dynamic_list = []
        
        # 1. Groq
        groq_key = get_key('GROQ_API_KEY')
        if groq_key:
            try:
                r = requests.get('https://api.groq.com/openai/v1/models', headers={'Authorization': f'Bearer {groq_key}'}, timeout=10)
                if r.status_code == 200:
                    for m in r.json().get('data', []):
                        mid = m['id'].lower()
                        if any(x in mid for x in ['llama', 'gemma', 'mistral', 'deepseek', 'qwen', 'gpt-oss', 'mixtral']):
                            if 'guard' not in mid:
                                dynamic_list.append({
                                    "provider_id": "groq",
                                    "display_name": f"Groq — {m['id']}",
                                    "model_id": m['id'],
                                    "requires_key": "GROQ_API_KEY",
                                    "is_free": True
                                })
            except Exception:
                pass
                
        # 2. OpenRouter
        or_key = get_key('OPENROUTER_API_KEY')
        if or_key:
            try:
                r = requests.get('https://openrouter.ai/api/v1/models', timeout=10)
                if r.status_code == 200:
                    for m in r.json().get('data', []):
                        # Strict free tier check
                        is_free = (m.get('pricing', {}).get('prompt', '0') == '0' and m.get('pricing', {}).get('completion', '0') == '0') or ':free' in m['id'].lower()
                        if is_free:
                            mid = m['id'].lower()
                            # Exclude moderation/embeddings/agents, keep only pure text LLMs
                            if 'moderation' not in mid and 'embed' not in mid:
                                name = m.get('name', m['id'])
                                dynamic_list.append({
                                    "provider_id": "openrouter",
                                    "display_name": f"OR — {name}"[:50],
                                    "model_id": m['id'],
                                    "requires_key": "OPENROUTER_API_KEY",
                                    "is_free": True
                                })
            except Exception:
                pass

        if dynamic_list:
            os.makedirs(os.path.dirname(DYNAMIC_MODELS_FILE), exist_ok=True)
            with open(DYNAMIC_MODELS_FILE, "w", encoding="utf-8") as f:
                json.dump(dynamic_list, f, indent=4)
            cls._load_dynamic_models()
            return len(dynamic_list)
        return 0

    @classmethod
    def _load_dynamic_models(cls):
        if not os.path.exists(DYNAMIC_MODELS_FILE):
            return
        try:
            with open(DYNAMIC_MODELS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Load dead models to avoid importing known bad models
            dead = set()
            try:
                base_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                dead_path = os.path.join(base_dir, "data", "dead_models.json")
                if os.path.exists(dead_path):
                    with open(dead_path, "r", encoding="utf-8") as f:
                        dead = set(json.load(f))
            except: pass

            # Remove previously loaded dynamic models (to avoid duplicates on refresh)
            cls.ALL_MODELS = [m for m in cls.ALL_MODELS if not getattr(m, "_is_dynamic", False)]
            
            for d in data:
                # Deduplicate by model_id and skip permanently dead models
                if d['display_name'] in dead:
                    continue
                if not any(m.model_id == d['model_id'] and m.provider_id == d['provider_id'] for m in cls.ALL_MODELS):
                    pm = ProviderModel(
                        provider_id=d['provider_id'],
                        display_name=d['display_name'],
                        model_id=d['model_id'],
                        requires_key=d['requires_key'],
                        is_free=d.get('is_free', False)
                    )
                    pm._is_dynamic = True
                    cls.ALL_MODELS.append(pm)
        except Exception:
            pass

ProviderRegistry._load_dynamic_models()


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
