import uuid
from fastapi import APIRouter,Depends, Form, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from schemas.auth import *
from sqlalchemy import select
from sqlalchemy.orm import joinedload,selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User
from models.token import BlacklistedToken, OutstandingToken
from database import get_db
from datetime import datetime,timedelta
from passlib.context import CryptContext
from config import setting



#We will use password creation mechanism of Django
pwd_context = CryptContext(schemes=["django_pbkdf2_sha256", "django_argon2", "django_bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/sw-login/")
oauth2_scheme.auto_error = False

async def get_current_user(
    token : str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    if token==None: return None
    try:
        payload = jwt.decode(token, setting.SECRET_KEY, algorithms=[setting.HASH_ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).options(joinedload(User.groups)).where(User.id == user_id))
    user = result.unique().scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user



def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now() + expires_delta
    to_encode.update({"exp": expire.timestamp(), "token_type": "access"})
    return jwt.encode(to_encode, setting.SECRET_KEY, algorithm=setting.HASH_ALGORITHM)

def create_refresh_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now() + expires_delta
    jti = str(uuid.uuid4())
    to_encode.update({
        "exp": expire.timestamp(),
        "jti": jti,
        "token_type": "refresh"
    })
    encoded = jwt.encode(to_encode, setting.SECRET_KEY, algorithm=setting.HASH_ALGORITHM)
    return encoded, jti, expire

def decode_token(token: str):
    return jwt.decode(token, setting.SECRET_KEY, algorithms=[setting.HASH_ALGORITHM])


def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def get_password_hash(password):
    return pwd_context.hash(password)

#Authentication endpoints router
router = APIRouter(
    prefix="/auth", 
    tags=["Authentication & Autherization"], 
)


@router.post("/sw-login")
async def login_sw(username: str = Form(...), password: str = Form(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == username))
    user = result.unique().scalar_one_or_none()
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    access_token = create_access_token({"user_id": user.id}, timedelta(minutes=setting.ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="User login and token generation",
    description="""
Authenticate a user and return both access and refresh JWT tokens.

- Access token: short-lived token for authorization
- Refresh token: used to obtain new access token

The user must provide valid `username` and `password`.
"""
)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).options(joinedload(User.groups)).where(User.username == data.username))
    user = result.unique().scalar_one_or_none()
    role = user.groups[0].name if user.groups else None
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token({"user_id": user.id}, timedelta(minutes=setting.ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token, jti, exp = create_refresh_token({"user_id": user.id}, timedelta(days=setting.REFRESH_TOKEN_EXPIRE_DAYS))

    db.add(OutstandingToken(
        jti=jti,
        token=refresh_token,
        expires_at=exp,
        user_id=user.id
    ))
    await db.commit()    
    return LoginResponse(**{"access": access_token, "refresh": refresh_token, "role": role})


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(token: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(token.refresh)
        if payload["token_type"] != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        jti = payload["jti"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(OutstandingToken).options(joinedload(OutstandingToken.blacklisted)).where(OutstandingToken.jti == jti))
    token_record = result.unique().scalar_one_or_none()
    if not token_record:
        raise HTTPException(status_code=401, detail="Token not recognized")
    if token_record.blacklisted:
        raise HTTPException(status_code=401, detail="Token has been blacklisted")

    new_access = create_access_token({"user_id": token_record.user_id}, timedelta(minutes=setting.ACCESS_TOKEN_EXPIRE_MINUTES))
    return RefreshResponse(access=new_access)


@router.post("/logout")
async def logout(Token: LogoutRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(Token.refresh)
        if payload["token_type"] != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token")
        jti = payload["jti"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(select(OutstandingToken).options(joinedload(OutstandingToken.blacklisted)).where(OutstandingToken.jti == jti))
    token_record = result.unique().scalar_one_or_none()
    if not token_record:
        raise HTTPException(status_code=404, detail="Token not found")

    if token_record.blacklisted:
        return {"detail": "Token already blacklisted"}

    db.add(BlacklistedToken(token_id=token_record.id))
    await db.commit()
    return {"detail": "Successfully logged out"}