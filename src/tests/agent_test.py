import asyncio
from src.agent import agent, AgentDeps
from src.db import UserProfile, db_manager

async def main():
    # Initialize the DB pool
    await db_manager.init_pool()
    pool = db_manager.get_pool()

    # Create a fake user profile (adjust fields as needed)
    user_profile = UserProfile(
        first_name="Test",
        last_name="User",
        availability="Full-time",
        bio="Aspiring actor",
        role="Actor",
        city="Los Angeles",
        country="USA"
    )

    # Example user message
    user_message = "Find me acting jobs in Los Angeles"

    # Acquire a DB connection
    async with pool.acquire() as conn:
        deps = AgentDeps(user_profile=user_profile, conn=conn)
        await agent.to_cli(prog_name="j*b search agent", deps=deps)

    # Close the DB pool
    await db_manager.close_pool()

if __name__ == "__main__":
    asyncio.run(main())