"""Unit tests for domain models."""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.ai_psadt_agent.domain_models.base import Base
from src.ai_psadt_agent.domain_models.package import (
    Package,
    PackageCreate,
    PackageUpdate,
    PackageResponse,
)


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


class TestPackageModel:
    """Test cases for Package SQLAlchemy model."""

    def test_package_creation(self, in_memory_db):
        """Test creating a Package instance."""
        package = Package(
            name="Test Package",
            version="1.0.0",
            installer_path="/path/to/installer.msi",
            script_text="# Test script content",
        )

        in_memory_db.add(package)
        in_memory_db.commit()

        # Verify the package was created with correct attributes
        assert package.id is not None
        assert package.name == "Test Package"
        assert package.version == "1.0.0"
        assert package.installer_path == "/path/to/installer.msi"
        assert package.script_text == "# Test script content"
        assert isinstance(package.created_at, datetime)
        assert isinstance(package.updated_at, datetime)

    def test_package_optional_fields(self, in_memory_db):
        """Test Package with optional fields as None."""
        package = Package(name="Minimal Package", version="0.1.0")

        in_memory_db.add(package)
        in_memory_db.commit()

        assert package.installer_path is None
        assert package.script_text is None


class TestPackagePydanticSchemas:
    """Test cases for Package Pydantic schemas."""

    def test_package_create_schema(self):
        """Test PackageCreate schema validation."""
        data = {
            "name": "Test Package",
            "version": "1.0.0",
            "installer_path": "/path/to/installer.msi",
            "script_text": "# Script content",
        }

        package_create = PackageCreate(**data)

        assert package_create.name == "Test Package"
        assert package_create.version == "1.0.0"
        assert package_create.installer_path == "/path/to/installer.msi"
        assert package_create.script_text == "# Script content"

    def test_package_response_schema(self, in_memory_db):
        """Test PackageResponse schema with SQLAlchemy model."""
        package = Package(
            name="Response Test Package",
            version="1.0.0",
            installer_path="/path/to/installer.msi",
            script_text="# Test script",
        )

        in_memory_db.add(package)
        in_memory_db.commit()

        # Convert to response schema
        response = PackageResponse.model_validate(package)

        assert response.id == package.id
        assert response.name == "Response Test Package"
        assert response.version == "1.0.0"
        assert response.installer_path == "/path/to/installer.msi"
        assert response.script_text == "# Test script"
        assert isinstance(response.created_at, datetime)
        assert isinstance(response.updated_at, datetime)
