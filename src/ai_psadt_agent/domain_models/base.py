from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):  # SQLAlchemy 2.x style
    """Shared metadata for all ORM models."""

    pass
