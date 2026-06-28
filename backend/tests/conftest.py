import os
import sys
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# Set fallback test values for any keys not present in .env
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_API_KEY", "test-anon-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-for-testing")
os.environ.setdefault("LLM_API_KEY", "test-llm-key")
os.environ.setdefault("SUPABASE_DB_URL", "postgresql://test:test@localhost/test")
os.environ.setdefault("LLM_MODEL", "test-model")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Patch supabase.create_client before auth_routes imports it at module level.
# auth_routes does `from supabase import create_client` — patching the source
# here ensures the imported name is the mock when auth_routes first loads.
_supabase_patcher = patch("supabase.create_client", return_value=MagicMock())
_supabase_patcher.start()
