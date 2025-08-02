"""
Automation Routes - API endpoints for automation management
"""

from fastapi import APIRouter

automation_router = APIRouter()

# Placeholder for future automation routes
@automation_router.get("/test")
async def test_automation():
    return {"message": "Automation routes working"}