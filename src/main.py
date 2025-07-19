from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import logfire

from src.core.config import settings
from src.db.session import db_manager
from src.api.v1 import endpoints

logger = logging.getLogger("uvicorn.error")
logfire.configure(token=settings.logfire_write_token)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await db_manager.init_pool()
        logger.info("App started with database connection.")
    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}")
        raise
    yield
    try:
        await db_manager.close_pool()
        logger.info("App shutdown.")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

app = FastAPI(lifespan=lifespan, title="My Chat Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

logfire.instrument_fastapi(app=app)


# Include the router from the api directory
app.include_router(endpoints.router, prefix="/api/v1")