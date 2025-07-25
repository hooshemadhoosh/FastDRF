from permissions.BasePermission import BasePermission


class IsAuthenticated(BasePermission):
    @classmethod
    async def has_permission(cls, user,*args):
        return user!=None
