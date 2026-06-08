from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import json
import logging
from datetime import datetime
from typing import Dict
from dotenv import load_dotenv

from api.diagnosis_routes import diagnosis_router
from api.auth_routes import router as auth_router
from managers.websocket_manager import ConnectionManager
from managers.model_manager import model_manager #Global variable to initiallize models here in main.py and carry over to diagnosis_routes.py for model usage
from nodes import LLMDiagnosisNode, ImageClassificationNode, FollowUpInteractionNode, OverallAnalysisNode, MedicalReportNode 
from contextlib import asynccontextmanager

load_dotenv()

# Simple logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    print("🚀 AI Medical Diagnosis API starting...")
    
    # Load all models once
    try:
        model_info = await model_manager.load_all_models()
        print(f"📊 Model loading summary:")
        print(f"   • Total load time: {model_info['load_time_seconds']}s")
        print(f"   • LLM model loaded: {model_info['local_adapter_loaded']}")
        print(f"   • Skin model: On-demand loading")  
        print(f"   • Embedding model: On-demand loading")  
        
        from api.diagnosis_routes import initialize_nodes_once
        initialize_nodes_once()
        print("✅ All nodes initialized with pre-loaded models!")
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        print("⚠️ API will start but models may not be available")
    
    print(f"📋 Available routes:")
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            print(f"   {list(route.methods)} {route.path}")
    print("✅ Startup complete!")
    
    yield 
    
    print("🛑 Shutting down API...")
    await model_manager.cleanup()
    print("✅ Shutdown complete!")

# Create FastAPI app
app = FastAPI(
    title="AI Medical Diagnosis Assistant",
    description="Medical AI system with LangGraph workflow",
    version="2.0.0",
    lifespan=lifespan
)

# Middleware setup
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(diagnosis_router)
app.include_router(auth_router)

# Global connection manager
manager = ConnectionManager()

# # WebSocket endpoint (keep in main.py as it's core infrastructure)
# @app.websocket("/ws/{session_id}")
# async def websocket_endpoint(websocket: WebSocket, session_id: str):
#     await manager.connect(websocket, session_id)
#     try:
#         while True:
#             # Keep connection alive and listen for client messages
#             data = await websocket.receive_text()
#             message = json.loads(data)
            
#             # Handle different message types
#             if message.get("type") == "ping":
#                 await manager.send_message(session_id, {
#                     "type": "pong",
#                     "timestamp": datetime.now().isoformat()
#                 })
#             elif message.get("type") == "workflow_status_request":
#                 await send_workflow_status(session_id)
            
#     except WebSocketDisconnect:
#         manager.disconnect(session_id)
#     except Exception as e:
#         print(f"❌ WebSocket error for {session_id}: {e}")
#         manager.disconnect(session_id)

async def send_workflow_status(session_id: str):
    """Send current workflow status to client"""
    if session_id in manager.session_workflows:
        workflow_data = manager.session_workflows[session_id]
        await manager.send_message(session_id, {
            "type": "workflow_status",
            "data": workflow_data,
            "timestamp": datetime.now().isoformat()
        })

#simple test endpoint to verify routing
@app.get("/")
async def root():
    return {
        "message": "AI Medical Diagnosis API",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "textual_analysis": "/patient/textual_analysis"
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("🏥 Starting AI Medical Diagnosis API...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)