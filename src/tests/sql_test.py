# Debugging block to test the SQL script directly
import asyncpg
import asyncio
import os

async def test_sql(user_id: str, dsn: str):
    pool = await asyncpg.create_pool(dsn=dsn)
    async with pool.acquire() as conn:
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
        row = await conn.fetchrow(query, user_id)
        print(dict(row) if row else None)
    await pool.close()

if __name__ == "__main__":
    # Set your test user_id and database DSN here
    test_user_id = os.environ.get("TEST_USER_ID", "usr_bollywood11")
    test_dsn = os.environ.get("TEST_DSN", "postgresql://myuser:mypassword@localhost:5432/mydb")
    asyncio.run(test_sql(test_user_id, test_dsn))