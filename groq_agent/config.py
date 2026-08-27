"""Configuration and environment initialization module.

Adheres to Single Responsibility Principle (SRP):
Only responsible for environment loading, encoding configuration, and logging setup.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Root directory of the project (parent of this groq_agent directory)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
LOGS_DIR = PROJECT_ROOT / "logs"


def setup_utf8_encoding() -> None:
    """Ensure UTF-8 output on Windows terminals to avoid character encoding errors."""
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass


def setup_logging(log_filename: str = "agent_groq.log") -> logging.Logger:
    """Configure and return a structured logger writing to the logs directory."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / log_filename

    logger = logging.getLogger("groq_agent")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger


def setup_environment() -> logging.Logger:
    """Load environment variables, configure UTF-8, setup logger, and verify API key."""
    setup_utf8_encoding()
    logger = setup_logging()

    print(f"Project root: {PROJECT_ROOT}")
    print(f"Using .env from: {ENV_PATH}")

    load_dotenv(dotenv_path=ENV_PATH)

    groq_key_present = bool(os.getenv("GROQ_API_KEY"))
    print(f"Groq API key found: {groq_key_present}")

    if not groq_key_present:
        logger.warning("GROQ_API_KEY is missing from the environment or .env file.")

    return logger


def get_logger() -> logging.Logger:
    """Retrieve the application logger."""
    return logging.getLogger("groq_agent")
