"""
Samay v5 FastAPI Backend
Main application with routes, middleware, and WebSocket support
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv
import os

# Import our core modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.local_assistant import LocalAssistant, ConversationContext, ComprehensiveResponse
from core.session_manager import SessionManager
from core.query_router import QueryRouter
from core.api_manager import APIServiceManager
from core.response_synthesizer import ResponseSynthesizer

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
local_assistant: Optional[LocalAssistant] = None
session_manager: Optional[SessionManager] = None
query_router: Optional[QueryRouter] = None
api_manager: Optional[APIServiceManager] = None
response_synthesizer: Optional[ResponseSynthesizer] = None

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session: {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session: {session_id}")

    async def send_personal_message(self, message: str, session_id: str):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

connection_manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Samay v5 backend...")
    
    global local_assistant, session_manager, query_router, api_manager, response_synthesizer
    
    try:
        # Initialize core components
        local_assistant = LocalAssistant()
        session_manager = SessionManager()
        query_router = QueryRouter()
        api_manager = APIServiceManager()
        response_synthesizer = ResponseSynthesizer()
        
        logger.info("All core components initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Samay v5 backend...")
    if local_assistant:
        await local_assistant.close()
    if api_manager:
        await api_manager.close()


# FastAPI app with lifespan
app = FastAPI(
    title="Samay v5 API",
    description="Next-Generation API-First AI Assistant",
    version="5.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
)


# Pydantic models
class QueryRequest(BaseModel):
    query: str = Field(..., description="User query to process")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    user_id: str = Field(default="default", description="User identifier")
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict, description="User preferences")


class QueryResponse(BaseModel):
    success: bool
    session_id: str
    stage: str
    content: str
    metadata: Dict[str, Any]
    error: Optional[str] = None


class ConversationResponse(BaseModel):
    success: bool
    session_id: str
    comprehensive_response: Dict[str, Any]
    processing_time: float
    service_responses: List[Dict[str, Any]]
    error: Optional[str] = None


class ServiceStatusResponse(BaseModel):
    services: Dict[str, str]
    total_services: int
    available_services: int
    last_updated: float


class SessionResponse(BaseModel):
    session_id: str
    created: bool
    expires_at: float
    metadata: Dict[str, Any]


# Dependency functions
def get_session_manager() -> SessionManager:
    if not session_manager:
        raise HTTPException(status_code=500, detail="Session manager not initialized")
    return session_manager


def get_local_assistant() -> LocalAssistant:
    if not local_assistant:
        raise HTTPException(status_code=500, detail="Local assistant not initialized")
    return local_assistant


def get_query_router() -> QueryRouter:
    if not query_router:
        raise HTTPException(status_code=500, detail="Query router not initialized")
    return query_router


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "5.0.0",
        "components": {
            "local_assistant": local_assistant is not None,
            "session_manager": session_manager is not None,
            "query_router": query_router is not None,
            "api_manager": api_manager is not None,
            "response_synthesizer": response_synthesizer is not None
        }
    }


# Session management endpoints
@app.post("/api/sessions", response_model=SessionResponse)
async def create_session(
    user_id: str = "default",
    metadata: Optional[Dict[str, Any]] = None,
    session_mgr: SessionManager = Depends(get_session_manager)
):
    """Create a new session"""
    try:
        session_id = session_mgr.create_session(user_id, metadata or {})
        session = session_mgr.get_session(session_id)
        
        return SessionResponse(
            session_id=session_id,
            created=True,
            expires_at=session.expires_at,
            metadata=session.metadata
        )
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}")
async def get_session_info(
    session_id: str,
    session_mgr: SessionManager = Depends(get_session_manager)
):
    """Get session information"""
    session = session_mgr.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "created_at": session.created_at,
        "last_active": session.last_active,
        "expires_at": session.expires_at,
        "is_active": session.is_active,
        "metadata": session.metadata
    }


@app.delete("/api/sessions/{session_id}")
async def invalidate_session(
    session_id: str,
    session_mgr: SessionManager = Depends(get_session_manager)
):
    """Invalidate a session"""
    success = session_mgr.invalidate_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session invalidated successfully"}


# Service status endpoints
@app.get("/api/services/status", response_model=ServiceStatusResponse)
async def get_service_status(
    session_mgr: SessionManager = Depends(get_session_manager)
):
    """Get status of all services"""
    status = session_mgr.get_service_status()
    available_count = sum(1 for s in status.values() if s.value in ['available', 'authenticated'])
    
    return ServiceStatusResponse(
        services={k: v.value for k, v in status.items()},
        total_services=len(status),
        available_services=available_count,
        last_updated=time.time()
    )


# Query processing endpoints
@app.post("/api/query/start", response_model=QueryResponse)
async def start_conversation(
    request: QueryRequest,
    assistant: LocalAssistant = Depends(get_local_assistant),
    session_mgr: SessionManager = Depends(get_session_manager)
):
    """Start a conversation with the local assistant"""
    try:
        # Validate or create session
        if request.session_id:
            session = session_mgr.get_session(request.session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
        else:
            request.session_id = session_mgr.create_session(request.user_id, request.preferences)
        
        # Start conversation
        context = await assistant.discuss_and_refine(
            request.query, 
            request.user_id, 
            request.session_id
        )
        
        # Prepare metadata - include browser automation metadata if present
        metadata = {
            "query_type": context.query_type.value,
            "original_query": context.original_query,
            "stage": context.stage.value
        }
        
        # Add browser automation metadata if present
        if hasattr(context, 'metadata') and context.metadata:
            metadata.update(context.metadata)
        
        return QueryResponse(
            success=True,
            session_id=context.session_id,
            stage=context.stage.value,
            content=context.conversation_history[-1]['content'] if context.conversation_history else "",
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(f"Failed to start conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class RefineQueryRequest(BaseModel):
    session_id: str = Field(..., description="Session ID for conversation continuity")
    user_response: str = Field(..., description="User response for query refinement")


@app.post("/api/query/refine", response_model=QueryResponse)
async def refine_query(
    request: RefineQueryRequest,
    assistant: LocalAssistant = Depends(get_local_assistant)
):
    """Refine query based on user feedback"""
    try:
        context = await assistant.refine_query(request.session_id, request.user_response)
        
        return QueryResponse(
            success=True,
            session_id=context.session_id,
            stage=context.stage.value,
            content=context.conversation_history[-1]['content'] if context.conversation_history else "",
            metadata={
                "refined_query": context.refined_query,
                "selected_services": context.selected_services,
                "stage": context.stage.value
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to refine query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ExecuteQueryRequest(BaseModel):
    session_id: str = Field(..., description="Session ID for conversation continuity")


@app.post("/api/query/execute", response_model=ConversationResponse)
async def execute_query(
    request: ExecuteQueryRequest,
    background_tasks: BackgroundTasks,
    assistant: LocalAssistant = Depends(get_local_assistant)
):
    """Execute the refined query across all services"""
    try:
        start_time = time.time()
        
        # Route to services
        service_responses = await assistant.route_to_services(request.session_id)
        
        # Synthesize responses
        comprehensive_response = await assistant.synthesize_all_responses(request.session_id, service_responses)
        
        processing_time = time.time() - start_time
        
        # Send WebSocket update
        background_tasks.add_task(
            notify_websocket_completion,
            request.session_id,
            comprehensive_response
        )
        
        return ConversationResponse(
            success=True,
            session_id=request.session_id,
            comprehensive_response={
                "original_query": comprehensive_response.original_query,
                "refined_query": comprehensive_response.refined_query,
                "synthesized_content": comprehensive_response.synthesized_content,
                "follow_up_suggestions": comprehensive_response.follow_up_suggestions,
                "sources": comprehensive_response.sources,
                "confidence_score": comprehensive_response.confidence_score
            },
            processing_time=processing_time,
            service_responses=[
                {
                    "service": resp.service,
                    "content": resp.content,
                    "status_code": resp.status_code,
                    "response_time": resp.response_time,
                    "error": resp.error
                }
                for resp in service_responses
            ]
        )
        
    except Exception as e:
        logger.error(f"Failed to execute query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query/complete", response_model=ConversationResponse)
async def complete_conversation(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    assistant: LocalAssistant = Depends(get_local_assistant),
    session_mgr: SessionManager = Depends(get_session_manager)
):
    """Complete end-to-end conversation flow"""
    try:
        start_time = time.time()
        
        # Create session if needed
        if not request.session_id:
            request.session_id = session_mgr.create_session(request.user_id, request.preferences)
        
        # Start conversation
        context = await assistant.discuss_and_refine(
            request.query, 
            request.user_id, 
            request.session_id
        )
        
        # Route to services
        service_responses = await assistant.route_to_services(request.session_id)
        
        # Synthesize responses
        comprehensive_response = await assistant.synthesize_all_responses(request.session_id, service_responses)
        
        processing_time = time.time() - start_time
        
        # Send WebSocket update
        background_tasks.add_task(
            notify_websocket_completion,
            request.session_id,
            comprehensive_response
        )
        
        return ConversationResponse(
            success=True,
            session_id=request.session_id,
            comprehensive_response={
                "original_query": comprehensive_response.original_query,
                "refined_query": comprehensive_response.refined_query,
                "synthesized_content": comprehensive_response.synthesized_content,
                "follow_up_suggestions": comprehensive_response.follow_up_suggestions,
                "sources": comprehensive_response.sources,
                "confidence_score": comprehensive_response.confidence_score,
                "total_response_time": comprehensive_response.total_response_time
            },
            processing_time=processing_time,
            service_responses=[
                {
                    "service": resp.service,
                    "content": resp.content,
                    "status_code": resp.status_code,
                    "response_time": resp.response_time,
                    "error": resp.error
                }
                for resp in service_responses
            ]
        )
        
    except Exception as e:
        logger.error(f"Failed to complete conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication"""
    await connection_manager.connect(websocket, session_id)
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            # Echo back for now (can be enhanced for real-time processing)
            await connection_manager.send_personal_message(
                f"Received: {data}",
                session_id
            )
            
    except WebSocketDisconnect:
        connection_manager.disconnect(session_id)


# Background task functions
async def notify_websocket_completion(session_id: str, comprehensive_response: ComprehensiveResponse):
    """Notify WebSocket clients when query processing is complete"""
    try:
        message = {
            "type": "query_complete",
            "session_id": session_id,
            "data": {
                "synthesized_content": comprehensive_response.synthesized_content,
                "confidence_score": comprehensive_response.confidence_score,
                "sources": comprehensive_response.sources
            }
        }
        
        await connection_manager.send_personal_message(
            str(message),
            session_id
        )
        
    except Exception as e:
        logger.error(f"Failed to send WebSocket notification: {e}")


# Query automation endpoints
@app.post("/api/automation/inject/{session_id}")
async def get_injection_commands(session_id: str):
    """Get JavaScript injection commands for query automation"""
    try:
        # Try to get automation engine
        try:
            from core.query_automation import get_automation_engine
            engine = await get_automation_engine()
            
            # Get session from active sessions
            if session_id in engine.active_sessions:
                session = engine.active_sessions[session_id]
                injection_commands = session["metadata"].get("injection_commands", [])
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "injection_commands": injection_commands,
                    "timestamp": time.time()
                }
            else:
                return {
                    "success": False,
                    "error": "Session not found in automation engine",
                    "session_id": session_id,
                    "timestamp": time.time()
                }
                
        except ImportError:
            logger.warning("Query automation not available")
            return {
                "success": False,
                "error": "Query automation engine not available",
                "session_id": session_id,
                "timestamp": time.time()
            }
            
    except Exception as e:
        logger.error(f"Error getting injection commands: {e}")
        return {
            "success": False,
            "error": str(e),
            "session_id": session_id,
            "timestamp": time.time()
        }

# Analytics endpoints
@app.get("/api/analytics/sessions")
async def get_session_analytics(
    session_mgr: SessionManager = Depends(get_session_manager)
):
    """Get session analytics"""
    stats = session_mgr.get_session_stats()
    return {
        "session_stats": stats,
        "timestamp": time.time()
    }


@app.get("/api/analytics/usage")
async def get_usage_analytics():
    """Get usage analytics"""
    # This would be enhanced with actual usage tracking
    return {
        "queries_today": 0,
        "queries_this_week": 0,
        "queries_this_month": 0,
        "avg_response_time": 0.0,
        "success_rate": 1.0,
        "timestamp": time.time()
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "timestamp": time.time()}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "timestamp": time.time()}
    )


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "localhost"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )