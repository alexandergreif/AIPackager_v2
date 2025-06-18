from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Package(Base):
    """SQLAlchemy model for Package resource."""

    __tablename__ = "packages"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(100), nullable=False)
    installer_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    script_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PackageCreate(BaseModel):
    """Pydantic schema for creating a package."""

    name: str
    version: str
    installer_path: Optional[str] = None
    script_text: Optional[str] = None


class PackageUpdate(BaseModel):
    """Pydantic schema for updating a package."""

    name: Optional[str] = None
    version: Optional[str] = None
    installer_path: Optional[str] = None
    script_text: Optional[str] = None


class PackageResponse(BaseModel):
    """Pydantic schema for package response."""

    id: int
    name: str
    version: str
    installer_path: Optional[str]
    script_text: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
