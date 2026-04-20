import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.database import engine, Base

# Import ALL models so Base.metadata knows about them before create_all()
import app.auth.models  # noqa: F401
import app.reports.models  # noqa: F401
import app.watchlist.models  # noqa: F401

from app.auth.router import router as auth_router
from app.research.router import router as research_router
from app.reports.router import router as reports_router
from app.watchlist.router import router as watchlist_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    logger.info("Starting up — creating database tables...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    yield


app = FastAPI(
    title="Investment Research Dashboard API",
    description="AI-powered financial research with structured insights",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware — allow all origins in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(research_router, prefix="/api/research", tags=["Research"])
app.include_router(reports_router, prefix="/api/reports", tags=["Reports"])
app.include_router(watchlist_router, prefix="/api/watchlist", tags=["Watchlist"])


@app.get("/api/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "Investment Research Dashboard API"}
