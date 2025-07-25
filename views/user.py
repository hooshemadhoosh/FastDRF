from typing import Callable
from pydantic import BaseModel
from sqlalchemy import select
from authentication import get_current_user
from database import get_db
from views.BaseViewSet import BaseViewSet, generate_pydantic_schema
from models.user import User

from fastapi import APIRouter, Depends, HTTPException,Query as Q,status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from permissions.auth import IsAuthenticated
from permissions.BasePermission import AllowAll

class UserCreateSchema(BaseModel):
    username: str
    password: str

class UserViewSet(BaseViewSet):
    target_query = select(User)
    perotect_by = IsAuthenticated & AllowAll
    search_fields = ["first_name","username"]
    ordering_fields = ["username","first_name","last_name"]
    default_ordering = "date_joined"
    create_request_schema = UserCreateSchema
    update_request_schema = generate_pydantic_schema(User,"UserUpdateSchema",include_relationships=False,read_only=True,exclude={"date_joined","last_login","id","username"})
    def _post(self)->Callable:
        async def post(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
            pass
        return post