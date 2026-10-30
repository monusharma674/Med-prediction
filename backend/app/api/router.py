from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.reports import router as reports_router
from app.api.v1.extraction import router as extraction_router
from app.api.v1.predictions import router as predictions_router
from app.api.v1.blockchain import router as blockchain_router
from app.api.v1.sharing import router as sharing_router
from app.api.v1.admin import router as admin_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(reports_router)
api_router.include_router(extraction_router)
api_router.include_router(predictions_router, prefix="/predictions", tags=["predictions"])
api_router.include_router(blockchain_router, prefix="/blockchain", tags=["blockchain"])
api_router.include_router(sharing_router, prefix="/sharing", tags=["sharing"])
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
