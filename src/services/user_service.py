import asyncpg
from typing import Optional
import logging
from src.schemas.user import UserProfile # <-- Updated import

logger = logging.getLogger("uvicorn.error")

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
