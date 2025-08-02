"""
Health Routes - API endpoints for health monitoring
"""

from fastapi import APIRouter

health_router = APIRouter()

# Placeholder for future health routes
@health_router.get("/status")
async def health_status():
    return {"message": "Health routes working"}