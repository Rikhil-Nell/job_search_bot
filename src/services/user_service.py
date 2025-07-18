import asyncpg
from typing import Optional
import logging
from src.schemas.user import UserProfile

logger = logging.getLogger("uvicorn.error")

async def get_user_profile(user_id: str, pool: asyncpg.pool.Pool) -> Optional[UserProfile]:
    async with pool.acquire() as conn:
        # This query is updated to join job_role and aggregate skills
        query = """
            SELECT
                COALESCE(up."firstName", '') as first_name,
                COALESCE(up."lastName", '') as last_name,
                COALESCE(up."Availability", '') as availability,
                COALESCE(up."Bio", '') as bio,
                COALESCE(jr.name, '') as role,
                COALESCE(c.name, 'Not specified') as city,
                COALESCE(co.name, 'Not specified') as country,
                ARRAY_AGG(s.name) FILTER (WHERE s.name IS NOT NULL) as skills
            FROM user_profile up
            LEFT JOIN city c ON up.city_id = c.id
            LEFT JOIN country co ON up.country_id = co.id
            LEFT JOIN job_role jr ON up.job_role_id = jr.id
            LEFT JOIN skills s ON up.id = s.user_profile_id
            WHERE up.user_id = $1
            GROUP BY up.id, jr.name, c.name, co.name
            LIMIT 1
        """

        try:
            row = await conn.fetchrow(query, user_id)
            if row:
                profile_data = dict(row)
                # Ensure 'skills' is an empty list if the user has no skills, instead of None
                profile_data['skills'] = profile_data['skills'] or []
                return UserProfile(**profile_data)
            return None
        except Exception as e:
            logger.error(f"Error fetching user profile for user_id {user_id}: {e}")
            return None