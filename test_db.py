import asyncio
from app.database import async_session_maker
from app.models.user import User

async def test_connection():
    try:
        # Open an async session with the database
        async with async_session_maker() as session:
            # Create a mock user
            mock_user = User(
                name="Test Commuter",
                email="test.commuter@urbanflow.ai",
                social_cluster_tag="daily_commuter",
                carbon_credits=15.0
            )
            
            # Add the user to the session and commit to the database
            session.add(mock_user)
            await session.commit()
            
            print("Connection Successful! Mock user created successfully.")
            
    except Exception as e:
        print(f"Database connection or insertion failed! Error details:")
        print(e)

if __name__ == "__main__":
    # Since our database operations are asynchronous, we run them using asyncio
    asyncio.run(test_connection())
