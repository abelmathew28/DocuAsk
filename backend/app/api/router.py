from fastapi import APIRouter

from app.api.v1 import auth, conversations, documents, intelligence, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(documents.router)
api_router.include_router(conversations.router)
api_router.include_router(intelligence.router)
api_router.include_router(users.router)
