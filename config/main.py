from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM_MODEL = "gemini-2.5-flash"

if not GEMINI_API_KEY:
    raise RuntimeError("Missing environment variables")