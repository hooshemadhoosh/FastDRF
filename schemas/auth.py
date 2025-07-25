from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=6, max_length=128)
class LoginResponse(BaseModel):
    refresh: str 
    access: str
    role: str

class RefreshRequest(BaseModel):
    refresh:str
class RefreshResponse(BaseModel):
    access:str

class LogoutRequest(BaseModel):
    refresh:str