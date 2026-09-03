import sys

# Windows consoles can default to cp1252; non-ASCII log output (emoji) would
# raise UnicodeEncodeError inside request handlers. Force UTF-8 regardless of
# how the server is launched.
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import os

from dotenv import load_dotenv
load_dotenv()

# MediSage stores no patient data. LangSmith tracing would ship every node run
# -- including the full symptom narrative -- to a third-party cloud and retain
# it there, silently defeating that guarantee. Disabled in code rather than
# left to a .env flag, and set before langchain/langgraph import so the
# tracing client never activates.
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGSMITH_TRACING"] = "false"

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from langgraph.checkpoint.memory import MemorySaver

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.diagnosis_routes import diagnosis_router, limiter
from config import settings

if settings.APP_ENV == "production":
    logging.basicConfig(
        level=logging.INFO,
        format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":%(message)r}',
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AI Medical Diagnosis API starting...")

    if not settings.LLM_API_KEY:
        logger.warning("LLM_API_KEY not set - LLM calls will fail at runtime")
    else:
        try:
            from llm.client import llm_client
            await llm_client.complete([{"role": "user", "content": "ping"}], max_tokens=5)
            logger.info(f"LLM connectivity confirmed (model: {settings.LLM_MODEL})")
        except Exception as e:
            logger.warning(f"LLM health ping failed: {e}")

    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.aclose()
        logger.info("Redis connected")
    except Exception as e:
        logger.warning(f"Redis ping failed: {e} - rate limiting uses in-memory fallback")

    # MediSage is fully anonymous: it stores no health data anywhere. The
    # checkpointer holds graph state — patient_text included — so it is
    # deliberately in-process only. Consequences, by design:
    #   - every in-flight session is LOST on restart, redeploy or crash, and
    #     clients mid-flow get 404 "Session not found" on their next call;
    #   - state is per-worker, so more than one worker requires sticky
    #     sessions (or a single worker) or requests will land on a process
    #     that has never heard of the session.
    # Do not swap this back for a database-backed saver: that would put the
    # patient's symptom text back on disk under a different name.
    checkpointer = MemorySaver()
    from graphs.diagnosis_workflow import compile_diagnosis_workflow
    app.state.diagnosis_graph = compile_diagnosis_workflow(checkpointer)
    logger.info("Diagnosis workflow graph compiled with in-memory checkpointer (no persistence)")
    logger.info("Startup complete!")
    yield

    logger.info("Shutdown complete!")


app = FastAPI(
    title="MediSage API",
    description="AI-assisted medical differential and evidence report for pre-consultation triage. Not a certified medical device.",
    version="2.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(diagnosis_router)


@app.get("/")
async def root():
    return {
        "message": "MediSage evidence-based medical differential API",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "start": "/diagnosis/start",
            "answers": "/diagnosis/{session_id}/answers",
            "finalize": "/diagnosis/{session_id}/finalize",
            "export": "/patient/export_report",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
