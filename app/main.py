# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
import uvicorn

from app.config.config import settings
from app.database.db import engine
from app.api.routers.v1 import login, registrations, learnings
from app.models import registration, tokens 


# -------------------------------------------------------
# Lifespan — runs on startup and shutdown
# -------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"📦 Database connected on port 5433")
    logger.info(f"📖 Docs available at http://localhost:8000/docs")
    logger.info(f"🔧 Debug mode: {settings.DEBUG}")

    yield  # app runs here

    # --- SHUTDOWN ---
    await engine.dispose()
    logger.info("👋 Shutting down — DB connections closed")


# -------------------------------------------------------
# App instance
# -------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for Personal Learning & Career Growth Dashboard",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# -------------------------------------------------------
# CORS Middleware
# -------------------------------------------------------
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------
# Routers 
# -------------------------------------------------------

app.include_router(registrations.router, prefix="/api/v1/registration", tags=["Registration"])
app.include_router(login.router, prefix="/api/v1/auth", tags=["Login"])
app.include_router(learnings.router, prefix="/api/v1/sessions", tags=["Learnings"])

# -------------------------------------------------------
# Health Check
# -------------------------------------------------------
@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }

@app.get("/api/v1/health", tags=["Health"])
def api_health():
    return {"status": "ok", "api_version": "v1"}


# -------------------------------------------------------
# Entry point
# -------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )