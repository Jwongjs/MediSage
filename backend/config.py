import os

class Settings:
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    # Fallback only: the startup/health ping and any client built without an
    # explicit model. Every graph node names its own model below.
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen/qwen3.8-27b")

    # One model per node, because Groq meters rate limits PER MODEL. Four nodes
    # sharing one model share one bucket, so the pipeline throttles itself; four
    # nodes on four models draw on four independent allowances. The split below
    # is not arbitrary -- it is constrained by which nodes can survive a
    # REASONING model, which spends a variable and sometimes large share of
    # max_tokens on hidden tokens before emitting anything visible:
    #
    #   generous budget -> safe for a reasoning model (B: 2500, C: 2000)
    #   tight budget    -> NOT safe (A: 500 then JSON, Summary: 120 then regex)
    #
    # so the two gpt-oss (reasoning) models take B and C, and the two qwen
    # (non-reasoning) models take A and Summary. Swapping a reasoning model onto
    # A or Summary fails quietly rather than loudly: Summary's two regexes miss
    # and severity reports "unknown" on every run with no error raised.
    #
    # All four are env-overridable: Groq retires model ids without notice, so a
    # dead id should cost a .env line, not a code change.
    DIFFERENTIAL_LLM_MODEL: str = os.getenv("DIFFERENTIAL_LLM_MODEL", "qwen/qwen3.8-27b")
    PROFILE_LLM_MODEL: str = os.getenv("PROFILE_LLM_MODEL", "openai/gpt-oss-120b")
    EVIDENCE_LLM_MODEL: str = os.getenv("EVIDENCE_LLM_MODEL", "openai/gpt-oss-20b")
    # How much of Node B's output budget gpt-oss may spend on hidden reasoning.
    # Paired with PROFILE_LLM_MODEL, not independent of it: a non-reasoning
    # model rejects this parameter outright, so a swap to qwen there needs this
    # set empty in the same breath. Empty means "do not send it".
    PROFILE_REASONING_EFFORT: str = os.getenv("PROFILE_REASONING_EFFORT", "low")
    SUMMARY_LLM_MODEL: str = os.getenv("SUMMARY_LLM_MODEL", "qwen/qwen3.8-27b")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    ALLOWED_ORIGINS: list[str] = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:3001,http://localhost:5173",
    ).split(",")
    APP_ENV: str = os.getenv("APP_ENV", "development")

settings = Settings()
