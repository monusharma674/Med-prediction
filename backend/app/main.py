import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database.session import Base, engine, SessionLocal
from app.api.router import api_router
from app.services.authentication.auth_service import AuthService
from app.models import *  # ensure all ORM models are registered with Base metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes database schema and ensures admin seed on startup."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    if settings.APP_ENV != "testing":
        # Create tables automatically for local development
        Base.metadata.create_all(bind=engine)

        # Seed default administrator if not present
        db = SessionLocal()
        try:
            AuthService.seed_admin(
                db=db,
                email=settings.ADMIN_EMAIL,
                password=settings.ADMIN_PASSWORD,
                name=settings.ADMIN_NAME,
            )
        finally:
            db.close()

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for AI-Powered Medical Report Management, OCR, Multi-Disease Risk Prediction & Blockchain Verification",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["System Health"])
def health_check():
    """Health check endpoint to verify backend operational readiness."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.APP_ENV,
        "version": "1.0.0",
    }
