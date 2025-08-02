#!/usr/bin/env python3
"""
Samay v6 FastAPI Backend
Main application entry point with health endpoints and extension communication
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

from core.local_assistant import LocalAssistant
from core.synthesis_engine import SynthesisEngine
from core.followup_analyzer import FollowupAnalyzer
from routes.automation import automation_router
from routes.health import health_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Samay v6 API",
    description="Browser Extension Multi-AI Automation Backend",
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

# Global instances
local_assistant: Optional[LocalAssistant] = None
synthesis_engine: Optional[SynthesisEngine] = None
followup_analyzer: Optional[FollowupAnalyzer] = None

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

class SynthesisRequest(BaseModel):
    session_id: str
    responses: List[ServiceResponse]
    followups: Optional[List[ServiceResponse]] = None

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize all core components on startup"""
    global local_assistant, synthesis_engine, followup_analyzer
    
    logger.info("🚀 Starting Samay v6 Backend...")
    
    try:
        # Initialize core components
        logger.info("Initializing Local Assistant...")
        local_assistant = LocalAssistant()
        await local_assistant.initialize()
        
        logger.info("Initializing Synthesis Engine...")
        synthesis_engine = SynthesisEngine(local_assistant)
        
        logger.info("Initializing Followup Analyzer...")
        followup_analyzer = FollowupAnalyzer(local_assistant)
        
        logger.info("✅ All components initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize components: {e}")
        raise

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
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # Check Local Assistant
    try:
        if local_assistant and await local_assistant.health_check():
            health_status["components"]["local_assistant"] = "healthy"
        else:
            health_status["components"]["local_assistant"] = "unhealthy"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["local_assistant"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Synthesis Engine
    try:
        if synthesis_engine:
            health_status["components"]["synthesis_engine"] = "healthy"
        else:
            health_status["components"]["synthesis_engine"] = "not_initialized"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["synthesis_engine"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Followup Analyzer
    try:
        if followup_analyzer:
            health_status["components"]["followup_analyzer"] = "healthy"
        else:
            health_status["components"]["followup_analyzer"] = "not_initialized"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["followup_analyzer"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Add system info
    health_status["system"] = {
        "active_connections": len(active_connections),
        "memory_usage": "N/A",  # Could add psutil for memory monitoring
        "uptime": "N/A"         # Could track startup time
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
            "timestamp": datetime.utcnow().isoformat()
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
            message="Automation request received and forwarded to extension",
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
        "status": "active" if is_connected else "inactive"
    }

@app.post("/api/synthesis/generate")
async def generate_synthesis(request: SynthesisRequest):
    """Generate synthesis from multiple AI responses"""
    logger.info(f"🎯 Generating synthesis for session: {request.session_id}")
    
    try:
        if not synthesis_engine:
            raise HTTPException(status_code=503, detail="Synthesis engine not available")
        
        # Convert ServiceResponse objects to dict format
        responses_dict = {
            resp.service: resp.content for resp in request.responses
        }
        
        followups_dict = None
        if request.followups:
            followups_dict = {
                resp.service: resp.content for resp in request.followups
            }
        
        # Generate synthesis
        synthesis = await synthesis_engine.synthesize_responses(
            original=responses_dict,
            followups=followups_dict
        )
        
        # Send WebSocket update if connected
        if request.session_id in active_connections:
            await active_connections[request.session_id].send_json({
                "type": "synthesis_complete",
                "session_id": request.session_id,
                "synthesis": synthesis,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return {
            "session_id": request.session_id,
            "synthesis": synthesis,
            "source_count": len(request.responses),
            "followup_count": len(request.followups) if request.followups else 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Synthesis generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/followup/analyze")
async def analyze_for_followup(request: SynthesisRequest):
    """Analyze responses to determine if follow-up questions are needed"""
    logger.info(f"🔍 Analyzing responses for follow-up: {request.session_id}")
    
    try:
        if not followup_analyzer:
            raise HTTPException(status_code=503, detail="Followup analyzer not available")
        
        # Convert ServiceResponse objects to dict format
        responses_dict = {
            resp.service: resp.content for resp in request.responses
        }
        
        # Analyze for follow-up needs
        analysis = await followup_analyzer.analyze_responses(responses_dict)
        
        return {
            "session_id": request.session_id,
            "needs_followup": analysis.needs_followup,
            "reasoning": analysis.reasoning,
            "questions": analysis.questions if analysis.needs_followup else {},
            "confidence": analysis.confidence,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Followup analysis failed: {e}")
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

# Include additional routers (when created)
# app.include_router(automation_router, prefix="/api/automation", tags=["automation"])
# app.include_router(health_router, prefix="/api/health", tags=["health"])

if __name__ == "__main__":
    # Development server configuration
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    reload = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"🚀 Starting Samay v6 Backend on {host}:{port}")
    logger.info(f"📚 API Documentation: http://{host}:{port}/docs")
    logger.info(f"🔄 Auto-reload: {reload}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )