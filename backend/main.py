import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config.logger import logger
from backend.config.settings import settings
from backend.models.database import Base, engine

# Import routers (to be created in next phases)
# from backend.api import auth, users, beneficiaries, transactions, admin, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifecycle events"""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created/verified")

    yield

    # Shutdown
    logger.info("Shutting down application")
    await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": settings.app_version,
    }


# Include routers (uncomment as they are created)
# app.include_router(
#     auth.router,
#     prefix=f"{settings.api_prefix}/auth",
#     tags=["Authentication"]
# )
# app.include_router(
#     users.router,
#     prefix=f"{settings.api_prefix}/users",
#     tags=["Users"]
# )
# app.include_router(
#     beneficiaries.router,
#     prefix=f"{settings.api_prefix}/beneficiaries",
#     tags=["Beneficiaries"]
# )
# app.include_router(
#     transactions.router,
#     prefix=f"{settings.api_prefix}/transactions",
#     tags=["Transactions"]
# )
# app.include_router(
#     admin.router,
#     prefix=f"{settings.api_prefix}/admin",
#     tags=["Admin"]
# )
# app.include_router(
#     chat.router,
#     prefix=f"{settings.api_prefix}/chat",
#     tags=["Chat"]
# )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler caught: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
