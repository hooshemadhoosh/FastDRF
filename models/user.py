from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

# Association Table
user_group_table = Table(
    "auth_user_groups",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("auth_user.id")),
    Column("group_id", Integer, ForeignKey("auth_group.id"))
)
class Group(Base):
    __tablename__ = "auth_group"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship(
        back_populates="groups",
        secondary=user_group_table
    )

class User(Base):
    __tablename__ = "auth_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    password: Mapped[str] = mapped_column(String(128), nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(150), nullable=False, default='')
    last_name: Mapped[str] = mapped_column(String(150), nullable=False, default='')
    email: Mapped[str] = mapped_column(String(254), nullable=False, default='')
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    date_joined: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    groups: Mapped[list[Group]] = relationship(
        back_populates="users",
        secondary=user_group_table,
    )
    tokens: Mapped[list["OutstandingToken"]] = relationship(
        back_populates="user",
        cascade="delete, delete-orphan"
    )
