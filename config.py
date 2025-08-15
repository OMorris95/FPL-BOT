import os
from dotenv import load_dotenv

load_dotenv()

FPL_EMAIL = os.getenv("FPL_EMAIL")
FPL_PASSWORD = os.getenv("FPL_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TEAM_ID = "6638986"
USER_MODE = "suggest"  # Options: "suggest", "hybrid", "auto"