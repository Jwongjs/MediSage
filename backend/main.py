from contextlib import asynccontextmanager
import logging
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from api.diagnosis_routes import diagnosis_router
from api.auth_routes import router as auth_router
from config import settings

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("AI Medical Diagnosis API starting...")

    if not settings.LLM_API_KEY:
        print("WARNING: LLM_API_KEY not set - LLM calls will fail at runtime")
    else:
        try:
            from llm.client import llm_client
            await llm_client.complete([{"role": "user", "content": "ping"}], max_tokens=5)
            print(f"LLM connectivity confirmed (model: {settings.LLM_MODEL})")
        except Exception as e:
            print(f"WARNING: LLM health ping failed: {e}")

    if not settings.SUPABASE_DB_URL:
        raise RuntimeError("SUPABASE_DB_URL is required for workflow state persistence")

    async with AsyncPostgresSaver.from_conn_string(settings.SUPABASE_DB_URL) as checkpointer:
        await checkpointer.setup()
        from graphs.patient_workflow import compile_patient_workflow
        app.state.patient_graph = compile_patient_workflow(checkpointer)
        print("Patient workflow graph compiled with Supabase checkpointer")
        print("Startup complete!")
        yield

    print("Shutdown complete!")


app = FastAPI(
    title="AI Medical Diagnosis Assistant",
    description="Medical AI system with LangGraph workflow",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
