import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve API keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("Warning: ANTHROPIC_API_KEY not found in environment variables")
else:
    # Set the API key in the environment for the library to use
    os.environ["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY
    print("Successfully loaded ANTHROPIC_API_KEY from environment")

# Database paths
DB_PATH = os.getenv("DB_PATH", "db/finances.db")

# Other configuration settings
LLM_MODEL = os.getenv("LLM_MODEL", "claude-3-5-haiku-latest")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0")) 