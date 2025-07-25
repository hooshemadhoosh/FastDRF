from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from database import Base

class OutstandingToken(Base):
    __tablename__ = 'token_blacklist_outstandingtoken'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    token: Mapped[str] = mapped_column(String, nullable=False)
    jti: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('auth_user.id'), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="tokens")
    blacklisted: Mapped["BlacklistedToken"] = relationship("BlacklistedToken",back_populates="token")

class BlacklistedToken(Base):
    __tablename__ = 'token_blacklist_blacklistedtoken'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    token_id: Mapped[int] = mapped_column(ForeignKey('token_blacklist_outstandingtoken.id'), nullable=False, unique=True)
    blacklisted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    token: Mapped[OutstandingToken] = relationship("OutstandingToken", back_populates="blacklisted")