from functools import wraps
from fastapi import APIRouter, Depends, HTTPException,Query as Q,status
from pydantic import BaseModel, Field, create_model
from sqlalchemy import func as f, or_, select
from sqlalchemy.orm import Session,DeclarativeMeta
from sqlalchemy.sql import Select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Callable, Dict, List, Optional, Set, Type
from schemas.DefaultSchemas import ListResponse,EmptySchema
from enum import Enum

class Method(str,Enum):
    read = "read"
    get = "get"
    create = "create"
    delete = "delete"
    update = "update"
    post = "post"

from authentication import get_current_user
from models.user import User
from database import get_db
from permissions.BasePermission import AllowAll, BasePermission




def get_target_models(stmt: Select) -> List[Type[DeclarativeMeta]]:
    models = []
    for col in stmt._raw_columns:
        if isinstance(col, type) and hasattr(col, '__mapper__'):
            models.append(col)            
        elif hasattr(col, 'entity_namespace') and hasattr(col.entity_namespace, '__mapper__'):
            models.append(col.entity_namespace)

    return models

def get_read_desc(search_fields: List[str],ordering_fields: List[str],default_ordering:str):
    description = "Valid ordering fields are:\n"
    for field in ordering_fields:   description+=f"- `{field}`\n\n"
    description+="\nSearching is done in fields:\n"
    for field in search_fields:   description+=f"- `{field}`\n\n"
    description+=f"\nDefault ordering field is: `{default_ordering}`"
    return description

def generate_pydantic_schema(
    model: Type[DeclarativeMeta],
    schema_name: str,
    include_relationships: bool = False,
    include: Optional[Set[str]] = None,
    exclude: Optional[Set[str]] = None,
    read_only: bool = False,
    created_schemas: Optional[Dict[str, Type[BaseModel]]] = None,
    depth: int = 1,
) -> Type[BaseModel]:
    """
    Generate a Pydantic schema from a SQLAlchemy model, optionally including relationships.

    Parameters:
    - model: SQLAlchemy declarative model class
    - schema_name: name of the generated schema
    - include_relationships: whether to include relationships
    - include: set of field names to include
    - exclude: set of field names to exclude
    - read_only: if True, all fields will be optional
    - created_schemas: cache for already created schemas to prevent circular recursion
    - depth: controls recursion depth for nested relationships
    """
    if created_schemas is None:
        created_schemas = {}

    if schema_name in created_schemas:
        return created_schemas[schema_name]

    fields = {}

    # Add scalar columns
    for column in model.__table__.columns:
        if include and column.name not in include:
            continue
        if exclude and column.name in exclude:
            continue

        python_type = column.type.python_type
        default = None if read_only or column.nullable else ...

        fields[column.name] = (Optional[python_type] if (read_only or column.nullable) else python_type, default)

    # Add relationships
    if include_relationships and depth > 0:
        for rel in model.__mapper__.relationships:
            if include and rel.key not in include:
                continue
            if exclude and rel.key in exclude:
                continue

            related_model = rel.mapper.class_
            related_schema_name = f"{related_model.__name__}NestedOut"
            nested_schema = generate_pydantic_schema(
                related_model,
                schema_name=related_schema_name,
                include_relationships=False,
                created_schemas=created_schemas,
                depth=depth - 1,
            )

            if rel.uselist:
                fields[rel.key] = (List[nested_schema], Field(default=[]))
            else:
                fields[rel.key] = (Optional[nested_schema], None)

    model_cls = create_model(schema_name, **fields)
    created_schemas[schema_name] = model_cls
    return model_cls




class BaseViewSet:
    target_query:   Select  = None
    target_model:   Type[DeclarativeMeta]
    read_response_schema:    Optional[Type[BaseModel]]   =   None
    get_response_schema:    Optional[Type[BaseModel]]   =   None
    create_request_schema:  Optional[Type[BaseModel]]   =   None
    create_response_schema: Optional[Type[BaseModel]]   =   None
    update_request_schema:  Optional[Type[BaseModel]]   =   None
    update_response_schema: Optional[Type[BaseModel]]   =   None
    post_response_schema:   Optional[Type[BaseModel]]   =   None
    delete_response_schema: Optional[Type[BaseModel]]   =   None

    search_fields:  Optional[list[str]] =   []
    ordering_fields:    Optional[list[str]] =   []
    default_ordering:   Optional[str]   =   None 

    exclude_methods: List[Method] = []

    perotect_by: BasePermission =   AllowAll
    description:   str =   ""
    def __init__(self, prefix: str, tags: list[str] = None):
        self.router = APIRouter(prefix=prefix, tags=tags or [])
        assert self.target_query!=None, "target_query must be defined in subclass"
        self.target_model = get_target_models(self.target_query)[0]
        if isinstance(self.perotect_by,type):   
            inst = self.perotect_by()
            self.perotect_by = inst
        self.openapi_tag_metadata = [{"name":tag,"description":self.description or f"*`{self.perotect_by.expression}`*"} for tag in tags]


        self.read_response_schema = self.read_response_schema or generate_pydantic_schema(self.target_model, f"{self.target_model.__name__}Read")
        self.get_response_schema = self.get_response_schema or generate_pydantic_schema(self.target_model, f"{self.target_model.__name__}Get")
        self.create_request_schema = self.create_request_schema or generate_pydantic_schema(self.target_model, f"{self.target_model.__name__}CreateReq", exclude=["id"])
        self.create_response_schema = self.create_response_schema or self.get_response_schema
        self.update_request_schema = self.update_request_schema or generate_pydantic_schema(self.target_model,f"{self.target_model.__name__}UpdateReq", exclude=["id"])
        self.update_response_schema = self.update_response_schema or self.get_response_schema
        self.post_response_schema = self.post_response_schema or EmptySchema
        self.delete_response_schema = self.delete_response_schema or EmptySchema

        if Method.read not in self.exclude_methods: self.router.get("",response_model=ListResponse[self.read_response_schema],description=get_read_desc(self.search_fields,self.ordering_fields,self.default_ordering))(self._build_method(self._read()))
        if Method.get not in self.exclude_methods:  self.router.get("/{item_id}",response_model=self.get_response_schema)(self._build_method(self._get()))
        if Method.create not in self.exclude_methods:   self.router.put("",response_model=self.create_response_schema)(self._build_method(self._create()))
        if Method.update not in self.exclude_methods:   self.router.patch("/{item_id}",response_model=self.update_response_schema)(self._build_method(self._update()))
        if Method.delete not in self.exclude_methods:   self.router.delete("/{item_id}",response_model=self.delete_response_schema)(self._build_method(self._delete()))
        if hasattr(self,"_post"):   self.router.post("",response_model=self.post_response_schema)(self._build_method(self._post()))

    async def _check_permissions(self, user: User, method: Method,db: AsyncSession,other_kwargs: dict):
        if not self.perotect_by==None and not await self.perotect_by.has_permission(user,method,self.target_query,db,other_kwargs):
            raise   HTTPException(403,{"status":"Access denied.","messages":list(set(self.perotect_by.messages))})

    def _build_method(self,func:Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            method_name = func.__name__
            await self._check_permissions(user=kwargs['user'],method=method_name,db=kwargs['db'],other_kwargs=kwargs)
            return await func(*args, **kwargs)
        return wrapper   

    def _read(self)->Callable:        
        async def read(offset: int = Q(0, ge=0),limit: int = Q(10, le=100),ordering: Optional[str] = Q(None),search: Optional[str] = Q(None),db: Session = Depends(get_db),user: User = Depends(get_current_user)):          
            stmt = self.target_query
            if ordering and ordering.lstrip("-") not in self.ordering_fields:
                raise HTTPException(status.HTTP_400_BAD_REQUEST,"The ordering field is not supported.")
            if search and self.search_fields:
                filters = []
                for field in self.search_fields:
                    filters.append(getattr(self.target_model, field).ilike(f"%{search}%"))
                stmt = stmt.where(or_(*filters))

            if ordering:
                col = getattr(self.target_model, ordering.lstrip("-"))
                stmt = stmt.order_by(col.desc() if ordering.startswith("-") else col.asc())
            elif self.default_ordering:
                stmt = stmt.order_by(getattr(self.target_model, self.default_ordering))
                
            subq = stmt.order_by(None).subquery()
            count_stmt = select(f.count()).select_from(subq)
            count = (await db.execute(count_stmt)).scalar_one()
            stmt = stmt.offset(offset).limit(limit)
            result = await db.execute(stmt)
            items = result.scalars().all()
            return ListResponse(count=count,result=items)
        return read
    
    def _get(self)->Callable:
        async def get(item_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
            stmt = self.target_query
            stmt = stmt.where(self.target_model.id == item_id)
            result = await db.execute(stmt)
            item = result.unique().scalar_one_or_none()
            if item==None:  raise   HTTPException(404,"Item not found.")
            return self.get_response_schema.model_validate(item, from_attributes=True)
        return get
    
    def _create(self)->Callable:
        schema = self.create_request_schema
        async def create(data: schema, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
            item = self.target_model(**data.model_dump())
            db.add(item)
            await   db.commit()
            await   db.refresh(item)
            return self.create_response_schema.model_validate(item, from_attributes=True)
        return create
    
    def _update(self)->Callable:
        schema = self.update_request_schema
        async def update(item_id: int, data: schema, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
            stmt = self.target_query
            stmt = stmt.where(self.target_model.id == item_id)
            result = await db.execute(stmt)
            item = result.unique().scalar_one_or_none()
            if item==None:  raise   HTTPException(404,"Item not found.")
            for k, v in data.model_dump(exclude_unset=True).items():
                setattr(item, k, v)
            await   db.commit()
            await   db.refresh(item)
            return self.update_response_schema.model_validate(item, from_attributes=True)
        return update
    
    def _delete(self)->Callable:
        async def delete(item_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
            stmt = self.target_query
            stmt = stmt.where(self.target_model.id == item_id)
            result = await db.execute(stmt)
            item = result.unique().scalar_one_or_none()
            if item==None:  raise   HTTPException(404,"Item not found.")
            await   db.delete(item)
            await   db.commit()
            return self.delete_response_schema()
        return delete