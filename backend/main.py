import sys

# Windows consoles can default to cp1252; non-ASCII log output (emoji) would
# raise UnicodeEncodeError inside request handlers. Force UTF-8 regardless of
# how the server is launched.
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.diagnosis_routes import diagnosis_router, limiter
from api.auth_routes import router as auth_router
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

    if not settings.SUPABASE_DB_URL:
        raise RuntimeError("SUPABASE_DB_URL is required for workflow state persistence")

    # A single long-lived connection (from_conn_string) gets dropped by Supabase's
    # idle timeout and is never reconnected, so the first checkpoint write after an
    # idle period fails with "the connection is closed". A pool recycles dead
    # connections; check_connection validates liveness before each checkout.
    connection_kwargs = {"autocommit": True, "prepare_threshold": 0}
    async with AsyncConnectionPool(
        conninfo=settings.SUPABASE_DB_URL,
        max_size=20,
        kwargs=connection_kwargs,
        check=AsyncConnectionPool.check_connection,
        open=False,
    ) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()
        from graphs.patient_workflow import compile_patient_workflow
        app.state.patient_graph = compile_patient_workflow(checkpointer)
        logger.info("Patient workflow graph compiled with Supabase checkpointer")
        from graphs.rag_chatbot import compile_rag_chatbot
        from api.chat_routes import chat_router
        app.state.rag_graph = compile_rag_chatbot()
        app.include_router(chat_router)
        logger.info("RAG chatbot graph compiled")
        logger.info("Startup complete!")
        yield

    logger.info("Shutdown complete!")


app = FastAPI(
    title="AI Medical Diagnosis Assistant",
    description="Medical AI system with LangGraph workflow",
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
app.include_router(auth_router)


@app.get("/")
async def root():
    return {
        "message": "AI Medical Diagnosis API",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "textual_analysis": "/patient/textual_analysis",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
