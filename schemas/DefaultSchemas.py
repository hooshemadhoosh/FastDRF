from typing import Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar("T")

class ListResponse(BaseModel, Generic[T]):
    count: int
    result: List[T]

class EmptySchema(BaseModel):
    pass