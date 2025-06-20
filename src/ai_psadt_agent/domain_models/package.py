import enum
import uuid
from datetime import datetime
from typing import Any, Optional, Union

from pydantic import BaseModel, field_serializer
from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class StatusEnum(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Package(Base):
    """SQLAlchemy model for Package resource."""

    __tablename__ = "packages"

    id: Mapped[int] = mapped_column(primary_key=True)
    package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(100), nullable=False)
    installer_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    script_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[StatusEnum] = mapped_column(Enum(StatusEnum), default=StatusEnum.PENDING, nullable=False)
    stage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status_message: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
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
    status: Optional[StatusEnum] = None
    stage: Optional[str] = None
    progress: Optional[int] = None
    status_message: Optional[str] = None


class PackageResponse(BaseModel):
    """Pydantic schema for package response."""

    id: int
    package_id: uuid.UUID
    name: str
    version: str
    installer_path: Optional[str]
    script_text: Optional[str]
    status: Union[StatusEnum, str]
    stage: Optional[str]
    progress: int
    status_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("status")
    def serialize_status(self, status: StatusEnum, _info: Any) -> str:
        return status.value

    @field_serializer("package_id")
    def serialize_package_id(self, package_id: uuid.UUID, _info: Any) -> str:
        return str(package_id)
