import os
import sys
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# Set fallback test values for any keys not present in .env
os.environ.setdefault("LLM_API_KEY", "test-llm-key")
os.environ.setdefault("SUPABASE_DB_URL", "postgresql://test:test@localhost/test")
os.environ.setdefault("LLM_MODEL", "test-model")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
