"""Integration tests for API endpoints."""

import json

import pytest
from ai_psadt_agent import create_app
from ai_psadt_agent.domain_models.base import Base
from ai_psadt_agent.domain_models.package import Package
from ai_psadt_agent.infrastructure.db.session import SessionLocal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def test_db():
    """Create a test database."""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(bind=engine)

    # Patch the session for testing
    original_session = SessionLocal
    import ai_psadt_agent.infrastructure.db.session as session_module

    session_module.SessionLocal = TestSessionLocal

    yield TestSessionLocal()

    # Restore original session
    session_module.SessionLocal = original_session


class TestHealthEndpoint:
    """Test cases for health endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/healthz")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["status"] == "ok"


class TestPackagesCRUDEndpoints:
    """Test cases for packages CRUD endpoints."""

    def test_create_package(self, client, test_db):
        """Test creating a new package."""
        package_data = {
            "name": "Test Package",
            "version": "1.0.0",
            "installer_path": "/path/to/installer.msi",
            "script_text": "# Test script content",
        }

        response = client.post(
            "/v1/packages",
            data=json.dumps(package_data),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = json.loads(response.data)

        assert data["name"] == "Test Package"
        assert data["version"] == "1.0.0"
        assert data["installer_path"] == "/path/to/installer.msi"
        assert data["script_text"] == "# Test script content"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_package(self, client, test_db):
        """Test getting a specific package by ID."""
        # First create a package
        package = Package(
            name="Get Test Package",
            version="1.0.0",
            installer_path="/path/to/installer.msi",
        )
        test_db.add(package)
        test_db.commit()

        response = client.get(f"/v1/packages/{package.id}")

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["id"] == package.id
        assert data["name"] == "Get Test Package"
        assert data["version"] == "1.0.0"
        assert data["installer_path"] == "/path/to/installer.msi"

    def test_list_packages(self, client, test_db):
        """Test listing all packages."""
        # Create test packages
        packages = [
            Package(name="Package A", version="1.0.0"),
            Package(name="Package B", version="2.0.0"),
            Package(name="Package C", version="3.0.0"),
        ]
        test_db.add_all(packages)
        test_db.commit()

        response = client.get("/v1/packages")

        assert response.status_code == 200
        data = json.loads(response.data)

        assert "packages" in data
        assert "total" in data
        assert "offset" in data
        assert "limit" in data
        assert len(data["packages"]) == 3
        assert data["total"] == 3

    def test_update_package(self, client, test_db):
        """Test updating a package."""
        # Create a package to update
        package = Package(name="Original Package", version="1.0.0")
        test_db.add(package)
        test_db.commit()

        update_data = {
            "name": "Updated Package",
            "version": "2.0.0",
            "script_text": "# Updated script",
        }

        response = client.put(
            f"/v1/packages/{package.id}",
            data=json.dumps(update_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["name"] == "Updated Package"
        assert data["version"] == "2.0.0"
        assert data["script_text"] == "# Updated script"

    def test_delete_package(self, client, test_db):
        """Test deleting a package."""
        package = Package(name="Delete Test Package", version="1.0.0")
        test_db.add(package)
        test_db.commit()
        package_id = package.id

        response = client.delete(f"/v1/packages/{package_id}")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["message"] == "Package deleted successfully"

    def test_docs_endpoint(self, client):
        """Test OpenAPI docs endpoint."""
        response = client.get("/docs")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "info" in data
        assert data["info"]["title"] == "PSADT AI Agent API"
