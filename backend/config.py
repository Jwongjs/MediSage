import os

class Settings:
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    SUPABASE_DB_URL: str = os.getenv("SUPABASE_DB_URL", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    ALLOWED_ORIGINS: list[str] = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:3001,http://localhost:5173",
    ).split(",")
    APP_ENV: str = os.getenv("APP_ENV", "development")

settings = Settings()
