"""Configuration module for the Expert AI App."""

import os
from pathlib import Path
from dotenv import load_dotenv

# --- CONSTANTS ---
HOST = "127.0.0.1"
PORT = 8000
UTF8 = "utf-8"
WINDOWS_OS = "win32"
ENV_FILE = ".env"
GROQ_API_KEY_VAR = "GROQ_API_KEY"

# File paths
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
REPORTS_DIR = BASE_DIR / "reports"

# Ensure directories exist
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables (looking in the parent directory where .env is stored)
PROJECT_ROOT = BASE_DIR.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ENV_FILE)

def get_groq_api_key() -> str:
    """Retrieve the Groq API key from the environment."""
    key = os.getenv(GROQ_API_KEY_VAR)
    if not key:
        raise ValueError("GROQ_API_KEY is not set in the .env file.")
    return key
