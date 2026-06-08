from fastapi import WebSocket
import json
from datetime import datetime
from typing import Dict

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_workflows: Dict[str, dict] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        print(f"🔌 WebSocket connected: {session_id}")
        
        # Send connection confirmation
        await self.send_message(session_id, {
            "type": "connection_established",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "message": "Connected to AI Medical Diagnosis System"
        })
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.session_workflows:
            del self.session_workflows[session_id]
        print(f"🔌 WebSocket disconnected: {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps(message))
            except Exception as e:
                print(f"❌ Failed to send message to {session_id}: {e}")
                self.disconnect(session_id)
    
    async def broadcast_to_session(self, session_id: str, message: dict):
        """Send message to specific session (future: can broadcast to multiple users)"""
        await self.send_message(session_id, message)