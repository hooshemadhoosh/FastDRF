from fastapi import APIRouter, Depends, HTTPException, Request,status
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from authentication import get_current_user
from models.user import User
from database import get_db



router = APIRouter()

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    if current_user==None:  return "anonymous"
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
    }