from fastapi import APIRouter, Depends, HTTPException
from asyncpg.pool import Pool

from src.schemas.user import ChatRequest
from src.services.user_service import get_user_profile
from src.services.chat_service import run_chat
from src.db.session import get_db_pool

router = APIRouter()

@router.post("/chat")
async def chat(request: ChatRequest, pool: Pool = Depends(get_db_pool)):
    # No more global variable checks needed!
    user_profile = await get_user_profile(request.user_id, pool)
    if not user_profile:
        raise HTTPException(404, detail="User profile not found")

    response = await run_chat(
        user_message=request.message,
        user_profile=user_profile,
        pool=pool
    )

    return response

@router.get("/health")
async def health(pool: Pool = Depends(get_db_pool)):
    # Optional: Actually test the database connection in health check
    try:
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": "disconnected", "error": str(e)}