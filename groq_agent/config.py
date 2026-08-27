"""Configuration module for the Groq Agent.

Purpose: 
This file handles the setup for our program before the AI starts. 
It loads secret keys (like API keys) and configures logging (saving output to a file).
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# --- CONSTANTS ---
# We use constants here to avoid "magic strings" in our code (Rule: No magic numbers/strings).
UTF8 = "utf-8"
WINDOWS_OS = "win32"
LOG_FILE_NAME = "agent_groq.log"
LOGGER_NAME = "groq_agent"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
ENV_FILE_NAME = ".env"
LOGS_FOLDER_NAME = "logs"
API_KEY_VAR_NAME = "GROQ_API_KEY"

# Calculate the paths to our project folders automatically.
# __file__ is this script. parent.parent goes up two folders to the main project folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ENV_FILE_NAME
LOGS_DIR = PROJECT_ROOT / LOGS_FOLDER_NAME


def setup_windows_console() -> None:
    """Configures the Windows terminal to support UTF-8 characters.
    
    Logic & Purpose:
    Modern AI models often output mathematical symbols (like ÷ or fractions). 
    The default Windows terminal crashes if it doesn't expect these symbols. 
    This forces the terminal to accept UTF-8 encoding.
    """
    if sys.platform == WINDOWS_OS:
        try:
            sys.stdout.reconfigure(encoding=UTF8)
            sys.stderr.reconfigure(encoding=UTF8)
        except Exception:
            pass


def setup_logger() -> logging.Logger:
    """Sets up a file logger to record everything the AI does.
    
    Logic & Purpose:
    We want to save a history of our agent's actions for debugging and learning.
    This creates a 'logs' folder and writes all events to 'agent_groq.log'.
    """
    # Create the logs directory if it doesn't exist
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file_path = LOGS_DIR / LOG_FILE_NAME

    # Create and configure the logger
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler(str(log_file_path), encoding=UTF8)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(file_handler)
        
    return logger


def prepare_environment() -> logging.Logger:
    """The main setup function that prepares everything needed to run the agent.
    
    Logic & Purpose:
    1. Fixes the Windows console.
    2. Sets up the logger.
    3. Loads the .env file which contains our secret API keys.
    """
    setup_windows_console()
    logger = setup_logger()

    print(f"Project root folder: {PROJECT_ROOT}")
    print(f"Loading environment variables from: {ENV_PATH}")

    # load_dotenv reads the .env file and adds its contents to the system environment
    load_dotenv(dotenv_path=ENV_PATH)

    # Check if the API key was successfully loaded
    has_api_key = bool(os.getenv(API_KEY_VAR_NAME))
    print(f"Groq API key loaded successfully: {has_api_key}")

    if not has_api_key:
        logger.warning(f"Warning: {API_KEY_VAR_NAME} is missing. The AI will not be able to connect.")

    return logger


def get_agent_logger() -> logging.Logger:
    """Returns the logger so other files can use it to record information."""
    return logging.getLogger(LOGGER_NAME)
