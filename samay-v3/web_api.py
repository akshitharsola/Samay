#!/usr/bin/env python3
"""
Samay v3 - FastAPI Web Backend
==============================
Modern web API wrapper for the Samay orchestrator system
"""

import os
import sys
import asyncio
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import our existing orchestrator components
from orchestrator.manager import SamaySessionManager
from orchestrator.prompt_dispatcher import PromptRequest


# Pydantic models for API requests/responses
class QueryRequest(BaseModel):
    prompt: str
    services: Optional[List[str]] = None
    confidential: bool = False
    timeout: int = 60
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    request_id: str
    session_id: str
    prompt: str
    total_time: float
    successful_services: int
    failed_services: int
    responses: List[Dict[str, Any]]
    reports: Optional[Dict[str, str]] = None
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    services: Dict[str, Dict[str, Any]]
    local_llm: Dict[str, Any]
    timestamp: str


class WebSocketMessage(BaseModel):
    type: str  # "query", "status", "result", "error"
    data: Dict[str, Any]
    session_id: str
    timestamp: str


# Initialize FastAPI app
app = FastAPI(
    title="Samay v3 API",
    description="Multi-Agent AI Assistant with Cloud and Local LLM Integration",
    version="3.0.0"
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the session manager
samay_manager = SamaySessionManager()

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}
conversation_history: Dict[str, List[Dict[str, Any]]] = {}


class ConnectionManager:
    """Manage WebSocket connections for real-time communication"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        print(f"🔌 WebSocket connected: {session_id}")
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            print(f"🔌 WebSocket disconnected: {session_id}")
    
    async def send_message(self, session_id: str, message: Dict[str, Any]):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps(message))
            except Exception as e:
                print(f"❌ Failed to send message to {session_id}: {e}")
                self.disconnect(session_id)
    
    async def broadcast_status(self, message: Dict[str, Any]):
        """Send status updates to all connected clients"""
        disconnected = []
        for session_id, connection in self.active_connections.items():
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"❌ Failed to broadcast to {session_id}: {e}")
                disconnected.append(session_id)
        
        # Clean up disconnected clients
        for session_id in disconnected:
            self.disconnect(session_id)


manager = ConnectionManager()


# API Routes
@app.get("/")
async def root():
    """Root endpoint - serve the frontend"""
    return {"message": "Samay v3 API is running", "version": "3.0.0"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Get system health status"""
    try:
        # Get service health
        service_health = samay_manager.health_check()
        
        # Get local LLM health
        local_llm_health = samay_manager.prompt_dispatcher.local_llm.health_check()
        
        return HealthResponse(
            status="healthy" if service_health else "degraded",
            services=service_health if isinstance(service_health, dict) else {},
            local_llm=local_llm_health,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, background_tasks: BackgroundTasks):
    """Process a query through the multi-agent system"""
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        # Store query in conversation history
        if session_id not in conversation_history:
            conversation_history[session_id] = []
        
        query_entry = {
            "type": "query",
            "content": request.prompt,
            "timestamp": datetime.now().isoformat(),
            "services": request.services,
            "confidential": request.confidential
        }
        conversation_history[session_id].append(query_entry)
        
        # Send status update via WebSocket
        await manager.send_message(session_id, {
            "type": "status",
            "data": {"message": "Processing query...", "stage": "started"},
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # Process the query
        result = samay_manager.multi_agent_query(
            prompt=request.prompt,
            services=request.services,
            timeout=request.timeout,
            confidential=request.confidential
        )
        
        # Store response in conversation history
        response_entry = {
            "type": "response",
            "content": result,
            "timestamp": datetime.now().isoformat()
        }
        conversation_history[session_id].append(response_entry)
        
        # Send result via WebSocket
        await manager.send_message(session_id, {
            "type": "result",
            "data": result,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
        
        return QueryResponse(
            request_id=result["request_id"],
            session_id=session_id,
            prompt=result["prompt"],
            total_time=result["total_time"],
            successful_services=result["successful_services"],
            failed_services=result["failed_services"],
            responses=result["responses"],
            reports=result.get("reports"),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        # Send error via WebSocket
        await manager.send_message(session_id, {
            "type": "error",
            "data": {"message": str(e)},
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/services")
async def get_services():
    """Get available services and their status"""
    try:
        summary = samay_manager.get_status_summary()
        return {
            "services": summary["services"],
            "total_services": summary["total_services"],
            "ready_services": summary["ready_services"],
            "local_llm_available": samay_manager.prompt_dispatcher.local_llm.is_available()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversation/{session_id}")
async def get_conversation_history(session_id: str):
    """Get conversation history for a session"""
    if session_id not in conversation_history:
        return {"session_id": session_id, "history": []}
    
    return {
        "session_id": session_id,
        "history": conversation_history[session_id]
    }


@app.delete("/conversation/{session_id}")
async def clear_conversation_history(session_id: str):
    """Clear conversation history for a session"""
    if session_id in conversation_history:
        del conversation_history[session_id]
    return {"message": "Conversation history cleared", "session_id": session_id}


@app.get("/reports/{report_path:path}")
async def get_report(report_path: str):
    """Serve generated reports"""
    report_file = Path("reports") / report_path
    if report_file.exists():
        return FileResponse(report_file)
    else:
        raise HTTPException(status_code=404, detail="Report not found")


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await manager.send_message(session_id, {
                    "type": "pong",
                    "data": {},
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                })
            
            elif message.get("type") == "status_request":
                # Send current system status
                health = await health_check()
                await manager.send_message(session_id, {
                    "type": "status_update",
                    "data": health.dict(),
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                })
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        print(f"❌ WebSocket error for {session_id}: {e}")
        manager.disconnect(session_id)


# Startup event handler
@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup"""
    print("🚀 Samay v3 Web API starting up...")
    print(f"📁 Working directory: {Path.cwd()}")
    print("🌐 API available at: http://localhost:8000")
    print("📡 WebSocket available at: ws://localhost:8000/ws/{session_id}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Samay v3 Web API shutting down...")
    # Close all WebSocket connections
    for session_id in list(manager.active_connections.keys()):
        manager.disconnect(session_id)


# Serve static files (frontend will be here)
@app.get("/ui")
async def serve_ui():
    """Serve the frontend UI"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Samay v3 - Multi-Agent AI Assistant</title>
        <style>
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: #f5f5f5; 
            }
            .container { 
                max-width: 800px; 
                margin: 0 auto; 
                background: white; 
                padding: 30px; 
                border-radius: 10px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { 
                color: #333; 
                text-align: center; 
                margin-bottom: 30px;
            }
            .status { 
                background: #e8f4f8; 
                padding: 15px; 
                border-radius: 5px; 
                margin: 20px 0; 
                border-left: 4px solid #007acc;
            }
            .button { 
                background: #007acc; 
                color: white; 
                padding: 10px 20px; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer; 
                margin: 5px;
                text-decoration: none;
                display: inline-block;
            }
            .button:hover { background: #005999; }
            .api-section { 
                margin: 20px 0; 
                padding: 15px; 
                background: #f8f9fa; 
                border-radius: 5px; 
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Samay v3 - Multi-Agent AI Assistant</h1>
            
            <div class="status">
                <h3>✅ System Status: Active</h3>
                <p>FastAPI backend is running and ready to serve requests.</p>
            </div>
            
            <div class="api-section">
                <h3>🔗 API Endpoints</h3>
                <ul>
                    <li><strong>Health Check:</strong> <a href="/health">/health</a></li>
                    <li><strong>Services Status:</strong> <a href="/services">/services</a></li>
                    <li><strong>Query Processing:</strong> POST /query</li>
                    <li><strong>WebSocket:</strong> ws://localhost:8000/ws/{session_id}</li>
                </ul>
            </div>
            
            <div class="api-section">
                <h3>🎯 Available Services</h3>
                <p>Multi-agent processing with Claude, Gemini, Perplexity + Local Phi-3-Mini</p>
                <ul>
                    <li>☁️ <strong>Cloud Services:</strong> Parallel processing across 3 AI services</li>
                    <li>🏠 <strong>Local LLM:</strong> Phi-3-Mini for confidential data processing</li>
                    <li>🔒 <strong>Privacy Mode:</strong> Local-only processing for sensitive data</li>
                </ul>
            </div>
            
            <div class="api-section">
                <h3>🚀 Next Steps</h3>
                <p>The React frontend is being developed. For now, you can:</p>
                <ol>
                    <li>Test API endpoints using the links above</li>
                    <li>Use the CLI interface: <code>python samay.py</code></li>
                    <li>Connect via WebSocket for real-time communication</li>
                </ol>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="/health" class="button">Check System Health</a>
                <a href="/services" class="button">View Services</a>
            </div>
        </div>
        
        <script>
            // Simple WebSocket test
            function testWebSocket() {
                const sessionId = 'test-' + Math.random().toString(36).substr(2, 9);
                const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);
                
                ws.onopen = function(event) {
                    console.log('WebSocket connected:', sessionId);
                    ws.send(JSON.stringify({type: 'ping', session_id: sessionId}));
                };
                
                ws.onmessage = function(event) {
                    console.log('WebSocket message:', JSON.parse(event.data));
                };
                
                ws.onclose = function(event) {
                    console.log('WebSocket closed');
                };
            }
            
            // Test WebSocket connection on page load
            testWebSocket();
        </script>
    </body>
    </html>
    """)


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Samay v3 Web API...")
    print("🌐 Frontend UI available at: http://localhost:8000/ui")
    print("📡 WebSocket endpoint: ws://localhost:8000/ws/{session_id}")
    print("📊 API docs: http://localhost:8000/docs")
    
    uvicorn.run(
        "web_api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )