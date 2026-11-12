from fastapi import APIRouter

from app.domains.ai_assistant.router import router as ai_router
from app.domains.community.router import router as community_router
from app.domains.events.router import router as events_router
from app.domains.identity.router import router as auth_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(ai_router)
api_router.include_router(community_router)
api_router.include_router(events_router)
