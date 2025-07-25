from abc import ABC, abstractmethod,ABCMeta
from typing import List
from fastapi import Request
from sqlalchemy import Select

from models.user import User
from views.BaseViewSet import Method
from sqlalchemy.ext.asyncio import AsyncSession

class BasePermissionMeta(ABCMeta):
    def __and__(cls, other):
        return AndPermission(cls, other)

    def __or__(cls, other):
        return OrPermission(cls, other)

    def __invert__(cls):
        return NotPermission(cls)

class BasePermission(ABC, metaclass=BasePermissionMeta):
    def __init__(self):
        self.failure_messages: list[str] = [f"The permission '{self.__class__.__name__}' has failed."]
        self.exp: str = self.__class__.__name__

    @property
    def messages(self):
        return self.failure_messages
    @messages.setter
    def messages(self, value: list[str]):
        self.failure_messages = value

    @property
    def expression(self) -> str:
        return self.exp
    @expression.setter
    def expression(self, value: str):
        self.exp = value
    
    @classmethod
    async def has_permission(cls, user:User,method:Method,target_query:Select,db:AsyncSession,other_kwargs:dict) -> bool:
        raise NotImplementedError("You must implement has_permission method")
    
class AndPermission(BasePermission):
    def __init__(self, *perms):
        self.perms = perms
        self.messages = []
        self.expression = f"({perms[0].__name__} & {perms[1].__name__})"

    async def has_permission(self, *args):
        result = True
        for perm in self.perms:
            perm_instance = perm() if isinstance(perm, type) else perm
            if not await perm_instance.has_permission(*args):
                self.messages+=perm_instance.messages
                result = False
        return result


class OrPermission(BasePermission):
    def __init__(self, *perms):
        self.perms = perms
        self.messages = []
        self.expression = f"({perms[0].__name__} | {perms[1].__name__})"

    async def has_permission(self, *args):
        result = False
        for perm in self.perms:
            perm_instance = perm() if isinstance(perm, type) else perm
            if await perm_instance.has_permission(*args):
                result = True
            else:
                self.messages+=perm_instance.messages
        return result


class NotPermission(BasePermission):
    def __init__(self, perm):
        self.perm = perm
        self.messages = []
        self.expression = f"~({perm.__name__})"

    async def has_permission(self, *args):
        perm_instance = self.perm() if isinstance(self.perm, type) else self.perm
        passed = await perm_instance.has_permission(*args)
        if passed:
            self.messages.append(f"NOT{perm_instance.messages}")
            return False
        return True
    

class AllowAll(BasePermission):
    @classmethod
    async def has_permission(cls, user,*args):
        return True
