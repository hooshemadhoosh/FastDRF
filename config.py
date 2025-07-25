from pydantic_settings import BaseSettings
#Theses setting variables should be set in a .env file at the same directory
class Settings(BaseSettings):
    DB_USER: str = "postgres"
    DB_PASS : str
    DB_HOST : str = "localhost"
    DB_PORT : int = 5432
    DB_NAME : str
    SECRET_KEY : str
    HASH_ALGORITHM: str = "HS256"  
    ACCESS_TOKEN_EXPIRE_MINUTES:int = 5
    REFRESH_TOKEN_EXPIRE_DAYS:int = 1
    class Config:
         env_file = ".env"

setting = Settings()

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from database import engine, Base,init_db
import authentication
from routers import test # Import the items router
from views.user import UserViewSet


@asynccontextmanager
async def lifespan(app: FastAPI):    
    await init_db()  
    yield


# Create the FastAPI app instance
app = FastAPI(
    title="Fast DRF",
    description="This is a fast version of Django Rest Framework.",
    version="1.0.0",
    lifespan=lifespan
)

views = [
    UserViewSet('/user',tags=["User Views"]),
]
app.openapi_tags = []
for view in views:  
    app.openapi_tags += view.openapi_tag_metadata
    app.include_router(view.router)

# Include normal routers
app.include_router(authentication.router)
app.include_router(test.router)

@app.get("/")
async def read_root():
    """
    Root endpoint for the API.
    """
    return {"message": "Welcome to the FastAPI Structured Application!"}