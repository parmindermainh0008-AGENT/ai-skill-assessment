"""
Configuration file — all API keys and settings are loaded from here.
Environment variables come from a .env file (local) or Streamlit secrets (deployment).
"""

import os
import pathlib
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

_SECRETS_FILE_EXISTS = pathlib.Path(".streamlit/secrets.toml").exists()


def get_secret(key: str, default: str = "") -> str:
    """
    Checks Streamlit secrets first (for deployment, if secrets.toml exists),
    then falls back to .env / environment variables (for local development).
    """
    if _SECRETS_FILE_EXISTS:
        try:
            if key in st.secrets:
                return st.secrets[key]
        except Exception:
            pass
    return os.getenv(key, default)


# Groq API key — get a free key at https://console.groq.com/keys
GROQ_API_KEY = get_secret("GROQ_API_KEY")

# Groq model — LLaMA 3.3 70B versatile is the best general-purpose choice
GROQ_MODEL = get_secret("GROQ_MODEL", "llama-3.3-70b-versatile")

# Google OAuth is now handled directly via the [auth] section in .streamlit/secrets.toml
# (using Streamlit's native st.login()) — no separate config needed here.


# SQLite database file
DB_PATH = get_secret("DB_PATH", "quiz_app.db")

# Difficulty levels available in the app
LEVELS = ["Beginner", "Intermediate", "Advanced"]

# Number of questions generated per quiz session
NUM_QUESTIONS = 5