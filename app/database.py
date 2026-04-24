import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# 1. Force load the .env from the current directory
load_dotenv(override=True) 

# 2. Extract and Validate the Database URL
raw_url = os.getenv("DATABASE_URL")

# --- OBSERVABILITY: Verify the connection type in terminal ---
if raw_url:
    print(f"--- [CLOUD ARCHITECT] Connecting to: {raw_url[:15]}... ---")
else:
    print("--- [ERROR] DATABASE_URL NOT FOUND IN .ENV! ---")

# --- STRICT REQUIREMENT: No Fallbacks / No SQLite ---
if not raw_url or "sqlite" in raw_url:
    raise ValueError(
        "CRITICAL ERROR: DATABASE_URL is missing or pointing to SQLite. "
        "Production Migration requires a valid Neon PostgreSQL connection string."
    )

# 3. TRANSFORM: Inject the Async Driver (asyncpg)
# SQLAlchemy 2.0 requires the driver to be explicitly named in the string.
DATABASE_URL = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# 4. NEON SSL CONFIG: Required for serverless cloud connections
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True only for deep debugging
    connect_args={"ssl": True} if "neon.tech" in DATABASE_URL else {}
)

# 5. COMPLIANCE: SQLAlchemy 2.0 async_sessionmaker
# We map the standard class to your app-specific variable name.
async_session_maker = async_sessionmaker(
    engine, 
    expire_on_commit=False, 
    class_=AsyncSession
)

Base = declarative_base()

async def get_db():
    """Dependency for getting async DB sessions in FastAPI routes."""
    async with async_session_maker() as session:
        yield session