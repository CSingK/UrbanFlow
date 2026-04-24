import asyncio
# We import exactly what we built in app/database.py
from app.database import async_session_maker, engine
from app.models.user import User

async def test_connection():
    print(f"--- Skeptic Check: Connecting to {engine.url.drivername} ---")
    
    try:
        # 1. Open the async session
        async with async_session_maker() as session:
            # 2. Create the mock user
            mock_user = User(
                name="Test Commuter",
                email="test.commuter@urbanflow.ai",
                social_cluster_tag="daily_commuter"
            )
            
            # 3. Add and Commit
            session.add(mock_user)
            await session.commit()
            
            print("✅ SUCCESS! Mock user reached Neon PostgreSQL in Singapore.")
            
    except Exception as e:
        print("❌ FAILED! The connection is still blocked.")
        print(f"Error details: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())