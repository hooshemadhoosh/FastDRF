import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker,DeclarativeBase
from config import setting 

#We use asyncpg as an asyncronous driver for SQLAlchamy
SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{setting.DB_USER}:{setting.DB_PASS}@{setting.DB_HOST}:{setting.DB_PORT}/{setting.DB_NAME}"

# Create the SQLAlchemy engine.
engine = create_async_engine(SQLALCHEMY_DATABASE_URL,echo=False)

# Create a SessionLocal class. Each instance of a SessionLocal class will be a database session.
# The class itself is not a database session yet.
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class. We will inherit from this class to create each of the
# database models (the ORM models).
class Base(DeclarativeBase):
    pass

#DB initializer function
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Dependency to get a DB session for each request.
# This will create a new session for each request and then close it when the request is finished.      
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()
    