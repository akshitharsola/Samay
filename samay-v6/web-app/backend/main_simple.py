#!/usr/bin/env python3
"""
Samay v6 FastAPI Backend - Simplified Version
Basic FastAPI application for testing without Ollama dependency
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Samay v6 API",
    description="Browser Extension Multi-AI Automation Backend (Simplified)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for extension communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "chrome-extension://*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

# Request/Response Models
class AutomationRequest(BaseModel):
    query: str
    session_id: str
    options: Dict = {}

class AutomationResponse(BaseModel):
    session_id: str
    status: str
    message: str
    data: Optional[Dict] = None

class ServiceResponse(BaseModel):
    service: str
    content: str
    timestamp: str
    word_count: int
    success: bool

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize basic components on startup"""
    logger.info("🚀 Starting Samay v6 Backend (Simplified)...")
    logger.info("✅ Basic components initialized successfully")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down Samay v6 Backend...")
    
    # Close all WebSocket connections
    for session_id, websocket in active_connections.items():
        try:
            await websocket.close()
        except Exception as e:
            logger.warning(f"Error closing WebSocket {session_id}: {e}")
    
    active_connections.clear()
    logger.info("✅ Shutdown complete")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic info"""
    return {
        "service": "Samay v6 API",
        "version": "1.0.0",
        "status": "running",
        "mode": "simplified",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "automation": "/api/automation/*",
            "websocket": "/ws/{session_id}"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "mode": "simplified",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "fastapi": "healthy",
            "websocket": "healthy",
            "local_assistant": "disabled (simplified mode)",
            "synthesis_engine": "disabled (simplified mode)",
            "followup_analyzer": "disabled (simplified mode)"
        },
        "system": {
            "active_connections": len(active_connections),
            "memory_usage": "N/A",
            "uptime": "N/A"
        }
    }
    
    return health_status

# WebSocket endpoint for real-time communication
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_connections[session_id] = websocket
    
    logger.info(f"📡 WebSocket connected: {session_id}")
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "mode": "simplified"
        })
        
        while True:
            # Keep connection alive and handle messages
            data = await websocket.receive_json()
            
            # Echo message for testing
            await websocket.send_json({
                "type": "echo",
                "original": data,
                "timestamp": datetime.utcnow().isoformat()
            })
            
    except WebSocketDisconnect:
        logger.info(f"📡 WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket error for {session_id}: {e}")
    finally:
        if session_id in active_connections:
            del active_connections[session_id]

# Automation endpoints
@app.post("/api/automation/start", response_model=AutomationResponse)
async def start_automation(request: AutomationRequest):
    """Start automation process"""
    logger.info(f"🚀 Starting automation for session: {request.session_id}")
    
    try:
        # Validate request
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Send WebSocket update if connected
        if request.session_id in active_connections:
            await active_connections[request.session_id].send_json({
                "type": "automation_started",
                "session_id": request.session_id,
                "query": request.query,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Return immediate response - actual automation handled by extension
        return AutomationResponse(
            session_id=request.session_id,
            status="started",
            message="Automation request received and forwarded to extension (simplified mode)",
            data={
                "query": request.query,
                "options": request.options,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Automation start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/automation/status/{session_id}")
async def get_automation_status(session_id: str):
    """Get automation status for session"""
    logger.info(f"📊 Status check for session: {session_id}")
    
    # Check if session has active WebSocket connection
    is_connected = session_id in active_connections
    
    return {
        "session_id": session_id,
        "connected": is_connected,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "active" if is_connected else "inactive",
        "mode": "simplified"
    }

@app.post("/api/synthesis/generate")
async def generate_synthesis(responses: List[ServiceResponse]):
    """Generate synthesis from multiple AI responses (simplified)"""
    logger.info(f"🎯 Generating synthesis from {len(responses)} responses (simplified mode)")
    
    try:
        # Simple fallback synthesis without local LLM
        synthesis = "# Multi-AI Response Synthesis (Simplified Mode)\n\n"
        
        for response in responses:
            synthesis += f"## {response.service.upper()} Response\n\n"
            synthesis += f"{response.content}\n\n"
        
        synthesis += "## Summary\n\n"
        synthesis += f"This synthesis combines responses from {len(responses)} AI services. "
        synthesis += "Each service provides unique perspectives on the query.\n\n"
        synthesis += f"*Generated: {datetime.utcnow().isoformat()} (Simplified Mode)*"
        
        return {
            "synthesis": synthesis,
            "source_count": len(responses),
            "timestamp": datetime.utcnow().isoformat(),
            "mode": "simplified"
        }
        
    except Exception as e:
        logger.error(f"❌ Synthesis generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"❌ Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    # Development server configuration
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    reload = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"🚀 Starting Samay v6 Backend (Simplified) on {host}:{port}")
    logger.info(f"📚 API Documentation: http://{host}:{port}/docs")
    logger.info(f"🔄 Auto-reload: {reload}")
    
    uvicorn.run(
        "main_simple:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )