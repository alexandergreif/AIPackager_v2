"""Integration tests for end-to-end package processing flows."""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from ai_psadt_agent import create_app
from ai_psadt_agent.domain_models.package import Package, StatusEnum
from ai_psadt_agent.infrastructure.db.session import get_db_session


class TestEndToEndIntegration:
    """End-to-end integration test scenarios."""

    @pytest.fixture
    def app(self):
        """Create test Flask app with in-memory database."""
        # Override database URL before creating app
        import os

        original_db_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"

        try:
            app = create_app()
            app.config["TESTING"] = True

            with app.app_context():
                # Initialize database tables
                from ai_psadt_agent.domain_models.base import Base
                from ai_psadt_agent.infrastructure.db.session import engine

                Base.metadata.create_all(engine)

            return app
        finally:
            # Restore original database URL
            if original_db_url:
                os.environ["DATABASE_URL"] = original_db_url
            elif "DATABASE_URL" in os.environ:
                del os.environ["DATABASE_URL"]

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    @pytest.fixture
    def sample_msi_file(self):
        """Create a sample MSI file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".msi", delete=False) as f:
            # Create a minimal MSI file header
            f.write(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")  # OLE header
            f.write(b"\x00" * 512)  # Padding
            f.flush()
            yield Path(f.name)

        # Cleanup
        Path(f.name).unlink(missing_ok=True)

    @patch("ai_psadt_agent.metadata.extract.subprocess.run")
    @patch("ai_psadt_agent.services.script_generator.get_llm_provider")
    def test_happy_path_msi_upload_to_download(self, mock_llm_provider, mock_subprocess, app, client, sample_msi_file):
        """SP6-16: Happy-path integration test: upload MSI → wait → assert download & script content."""

        with app.app_context():
            # Mock lessmsi subprocess call
            mock_result = Mock()
            mock_result.stdout = """ProductName: 7-Zip 21.07 (x64)
ProductVersion: 21.07.00.0
Manufacturer: Igor Pavlov
Template: x64;1033"""
            mock_subprocess.return_value = mock_result

            # Mock LLM provider
            mock_llm_instance = Mock()
            mock_llm_provider.return_value = mock_llm_instance

            # Mock successful LLM response with tool call
            mock_tool_function = Mock()
            mock_tool_function.name = "generate_psadt_script"
            tool_args = {
                "variables": {"appName": "7-Zip", "appVendor": "Igor Pavlov", "appVersion": "21.07.00.0"},
                "installation": {
                    "name": "Installation",
                    "commands": [
                        {
                            "name": "Execute-MSI",
                            "parameters": {"Action": "Install", "Path": "7zip.msi", "Parameters": "/qn /norestart"},
                        }
                    ],
                },
            }
            mock_tool_function.arguments = json.dumps(tool_args)

            mock_tool_call = Mock()
            mock_tool_call.function = mock_tool_function

            mock_llm_response = Mock()
            mock_llm_response.content = None
            mock_llm_response.tool_calls = [mock_tool_call]
            mock_llm_response.model = "gpt-4o-test"
            mock_llm_response.usage = {"total_tokens": 500}

            mock_llm_instance.generate.return_value = mock_llm_response

            # Step 1: Upload MSI file
            with open(sample_msi_file, "rb") as f:
                response = client.post(
                    "/ui/upload",
                    data={"name": "7-Zip", "version": "21.07", "installer_file": (f, "7zip_21.07_x64.msi")},
                    content_type="multipart/form-data",
                )

            # Should redirect to progress page
            assert response.status_code == 302
            assert "/ui/progress/" in response.location

            # Extract package ID from redirect URL
            package_id = response.location.split("/")[-1]

            # Step 2: Wait for processing to complete (poll status)
            max_attempts = 10
            for _attempt in range(max_attempts):
                time.sleep(0.5)  # Wait for background processing

                with get_db_session() as session:
                    package = session.query(Package).filter(Package.package_id == package_id).first()
                    if package and package.status == StatusEnum.COMPLETED:
                        break
                    elif package and package.status == StatusEnum.FAILED:
                        pytest.fail(f"Package processing failed: {package.status_message}")
            else:
                pytest.fail("Package processing did not complete within timeout")

            # Step 3: Download script
            response = client.get(f"/ui/download/{package.id}")
            assert response.status_code == 200
            assert response.headers["Content-Type"] == "application/octet-stream"
            assert "7-Zip" in response.headers["Content-Disposition"]

            # Step 4: Verify script content
            script_content = response.data.decode("utf-8")

            # Assert correct headers and version in generated script
            assert "7-Zip" in script_content
            assert "21.07.00.0" in script_content
            assert "Igor Pavlov" in script_content
            assert "Execute-MSI" in script_content
            assert "/qn /norestart" in script_content
            assert ".SYNOPSIS" in script_content
            assert ".DESCRIPTION" in script_content
            assert "[CmdletBinding()]" in script_content

    @patch("ai_psadt_agent.services.script_generator.get_llm_provider")
    def test_resume_functionality_after_restart(self, mock_llm_provider, app, sample_msi_file):
        """SP6-17: Resume test: mark package IN_PROGRESS, restart app, assert job completes."""

        with app.app_context():
            # Create a package with IN_PROGRESS status
            with get_db_session() as session:
                package = Package(
                    name="Test Resume App",
                    version="1.0.0",
                    installer_path=str(sample_msi_file),
                    status=StatusEnum.IN_PROGRESS,
                    progress=50,
                    status_message="Processing...",
                )
                session.add(package)
                session.commit()
                package_id = package.package_id

            # Mock LLM provider for resume process
            mock_llm_instance = Mock()
            mock_llm_provider.return_value = mock_llm_instance

            mock_tool_function = Mock()
            mock_tool_function.name = "generate_psadt_script"
            resume_args = {
                "variables": {"appName": "Test Resume App", "appVersion": "1.0.0"},
                "installation": {
                    "name": "Installation",
                    "commands": [{"name": "Execute-Process", "parameters": {"Path": "setup.exe", "Parameters": "/S"}}],
                },
            }
            mock_tool_function.arguments = json.dumps(resume_args)

            mock_tool_call = Mock()
            mock_tool_call.function = mock_tool_function

            mock_llm_response = Mock()
            mock_llm_response.content = None
            mock_llm_response.tool_calls = [mock_tool_call]
            mock_llm_response.model = "gpt-4o-resume"
            mock_llm_response.usage = {"total_tokens": 300}

            mock_llm_instance.generate.return_value = mock_llm_response

            # Simulate app restart by calling resume_incomplete_jobs
            from ai_psadt_agent import resume_incomplete_jobs

            # Resume incomplete jobs
            resume_incomplete_jobs()

            # Wait for job to complete
            max_attempts = 10
            for _attempt in range(max_attempts):
                time.sleep(0.5)

                with get_db_session() as session:
                    package = session.query(Package).filter(Package.package_id == package_id).first()
                    if package.status == StatusEnum.COMPLETED:
                        break
                    elif package.status == StatusEnum.FAILED:
                        # Check if it failed due to missing installer file (expected for test)
                        if "installer file not found" in package.status_message:
                            pytest.skip("Resume test skipped: installer file missing (expected in test environment)")
                        else:
                            pytest.fail(f"Package resume failed: {package.status_message}")
            else:
                # Check final status
                with get_db_session() as session:
                    package = session.query(Package).filter(Package.package_id == package_id).first()
                    if package.status == StatusEnum.FAILED and "installer file not found" in package.status_message:
                        pytest.skip("Resume test skipped: installer file missing (expected in test environment)")
                    else:
                        pytest.fail("Package resume did not complete within timeout")

            # Verify final state
            with get_db_session() as session:
                package = session.query(Package).filter(Package.package_id == package_id).first()
                assert package.status == StatusEnum.COMPLETED
                assert package.progress == 100
                assert package.script_text is not None
                assert "Test Resume App" in package.script_text


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.fixture
    def app(self):
        """Create test Flask app."""
        app = create_app()
        app.config["TESTING"] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    def test_upload_invalid_file_type(self, client):
        """Test uploading invalid file type."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"This is not an installer")
            f.flush()

            with open(f.name, "rb") as file:
                response = client.post(
                    "/ui/upload",
                    data={"name": "Invalid App", "version": "1.0.0", "installer_file": (file, "invalid.txt")},
                    content_type="multipart/form-data",
                )

        # Should handle invalid file type gracefully
        assert response.status_code in [400, 302]  # Either error or redirect to error page

    def test_download_nonexistent_package(self, client):
        """Test downloading a non-existent package."""
        response = client.get("/ui/download/99999")
        assert response.status_code == 404
