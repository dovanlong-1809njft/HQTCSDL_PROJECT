from fastapi import APIRouter

from app.domains.identity.router import router as auth_router

api_router = APIRouter()
api_router.include_router(auth_router)
