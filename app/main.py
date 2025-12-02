"""Main FastAPI Application"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api import router
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    if os.getenv("DISABLE_DB_INIT", "0") != "1":
        await init_db()
    yield


# Create FastAPI app
app = FastAPI(
    title="Visit Aqmola API",
    description="Tourism platform for Akmola Region",
    version="0.1.0",
    lifespan=lifespan
)

# Include API routes
app.include_router(router, prefix="/api/v1")


# Serve static files
@app.get("/")
async def root():
    """Serve main HTML page"""
    return FileResponse("src/web/index.html")


@app.get("/favicon.ico")
async def favicon():
    """Favicon placeholder"""
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=204, content=None)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
