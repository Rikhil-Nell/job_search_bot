import asyncpg
from pydantic import BaseModel
from typing import Optional
import logging
from src.core.config import settings

logger = logging.getLogger(__name__)
logger = logging.getLogger("uvicorn.error")

class DatabaseManager:
    def __init__(self):
        self.pool: Optional[asyncpg.pool.Pool] = None
   
    async def init_pool(self):
        self.pool = await asyncpg.create_pool(
            dsn=settings.db_url,
            min_size=5,
            max_size=20
        )
        logger.info("Database connection pool initialized.")
   
    async def close_pool(self):
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed.")
   
    def get_pool(self) -> asyncpg.pool.Pool:
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        return self.pool

db_manager = DatabaseManager()

async def get_db_pool() -> asyncpg.pool.Pool:
    return db_manager.get_pool()


class UserProfile(BaseModel):
    first_name: str = ""
    last_name: str = ""
    availability: str = ""
    bio: str = ""
    role: str = ""
    city: str = "Not specified"
    country: str = "Not specified"

async def get_user_profile(user_id: str, pool: asyncpg.pool.Pool) -> Optional[UserProfile]:
    async with pool.acquire() as conn:
        query = """
            SELECT
                COALESCE(up."firstName", '') as first_name,
                COALESCE(up."lastName", '') as last_name,
                COALESCE(up."Availability", '') as availability,
                COALESCE(up."Bio", '') as bio,
                COALESCE(up.role, '') as role,
                COALESCE(c.name, 'Not specified') as city,
                COALESCE(co.name, 'Not specified') as country
            FROM user_profile up
            LEFT JOIN city c ON up.city_id = c.id
            LEFT JOIN country co ON up.country_id = co.id  
            WHERE up.user_id = $1
            LIMIT 1
        """
        
        try:
            row = await conn.fetchrow(query, user_id)
            if row:
                # Convert the row to a dict and handle any None values
                profile_data = dict(row)
                return UserProfile(**profile_data)
            return None
        except Exception as e:
            logger.error(f"Error fetching user profile for user_id {user_id}: {e}")
            return None
