from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.db import db_manager, get_user_profile, get_db_pool
from src.agent import run_chat
from src.settings import settings
import logging
from contextlib import asynccontextmanager
import asyncpg
import logfire

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

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

logfire.instrument_fastapi(app=app)

class ChatRequest(BaseModel):
    user_id: str
    message: str

@app.post("/chat")
async def chat(request: ChatRequest, pool: asyncpg.pool.Pool = Depends(get_db_pool)):
    # No more global variable checks needed!
    user_profile = await get_user_profile(request.user_id, pool)
    if not user_profile:
        raise HTTPException(404, detail="User profile not found")
   
    async with pool.acquire() as conn:
        response = await run_chat(
            user_message=request.message,
            user_profile=user_profile,
            conn=conn
        )
        return response

@app.get("/health")
async def health(pool: asyncpg.pool.Pool = Depends(get_db_pool)):
    # Optional: Actually test the database connection in health check
    try:
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": "disconnected", "error": str(e)}