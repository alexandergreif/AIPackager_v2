"""Integration tests for the generation API endpoints."""

import json
import os  # Import os module
from unittest.mock import Mock, patch

import pytest
from ai_psadt_agent import create_app
from ai_psadt_agent.services.script_generator import GenerationResult


@pytest.fixture
def app():
    """Create test Flask app."""
    app_instance = create_app()
    app_instance.config["TESTING"] = True
    # Set a test API key for all tests in this module if not set by individual tests
    # This simplifies tests that don't specifically test auth.
    os.environ["API_KEY"] = "default-test-api-key"
    return app_instance


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def sample_installer_metadata():
    """Sample installer metadata for testing."""
    return {
        "name": "Test Application",
        "version": "1.0.0",
        "vendor": "Test Vendor",
        "installer_type": "msi",
        "installer_path": "test_app.msi",
        "silent_args": "/quiet /norestart",
        "architecture": "x64",
        "language": "EN",
    }


@pytest.fixture
def sample_generation_result():
    """Sample generation result for mocking."""
    return GenerationResult(
        structured_script=None,  # Added missing argument
        script_content="""
        <#
        .SYNOPSIS
            Test Application deployment script
        .DESCRIPTION
            Installs Test Application using PSADT
        #>
        [CmdletBinding()]
        Param (
            [Parameter(Mandatory=$false)]
            [String]$DeploymentType = 'Install'
        )
        Try {
            Set-ExecutionPolicy -ExecutionPolicy 'ByPass' -Scope 'Process' -Force
            ##*===============================================
            ##* VARIABLE DECLARATION
            ##*===============================================
            [String]$appVendor = 'Test Vendor'
            [String]$appName = 'Test Application'
            [String]$appVersion = '1.0.0'
            ##*===============================================
            ##* INSTALLATION
            ##*===============================================
            [String]$installPhase = 'Installation'
            Show-InstallationWelcome
            Show-InstallationProgress
            Execute-MSI -Action 'Install' -Path 'test_app.msi'
            Write-Log "Installation completed"
            Exit-Script -ExitCode 0
        }
        Catch {
            Write-Log "Error occurred"
            Exit-Script -ExitCode 1
        }
        """,
        metadata={
            "installer": {"name": "Test Application", "version": "1.0.0"},
            "llm_model": "gpt-4o",
            "llm_usage": {"total_tokens": 500},
            "attempt": 1,
        },
        validation_score=85.0,
        issues=[],
        suggestions=["Consider adding more detailed logging"],
        rag_sources=["psadt_fundamentals.md"],
    )


class TestGenerationAPI:
    """Test generation API endpoints."""

    TEST_API_KEY = "default-test-api-key"  # Consistent test key

    @patch("ai_psadt_agent.api.routes.generation.get_script_generator")
    def test_generate_script_success(
        self,
        mock_get_generator,
        client,
        sample_installer_metadata,
        sample_generation_result,
    ):
        """Test successful script generation."""
        mock_generator = Mock()
        mock_generator.generate_script.return_value = sample_generation_result
        mock_get_generator.return_value = mock_generator

        request_data = {
            "installer_metadata": sample_installer_metadata,
            "user_notes": "Please ensure silent installation",
            "save_to_package": False,
        }

        response = client.post(
            "/v1/generate",
            data=json.dumps(request_data),
            content_type="application/json",
            headers={"X-API-Key": self.TEST_API_KEY},
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "script_content" in data
        assert data["validation_score"] == 85.0

    def test_generate_script_missing_data(self, client):
        """Test generation with missing request data."""
        response = client.post(
            "/v1/generate",
            data="{}",
            content_type="application/json",
            headers={"X-API-Key": self.TEST_API_KEY},
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "No JSON data provided" in data["error"]

    def test_generate_script_invalid_data(self, client):
        """Test generation with invalid request data."""
        request_data = {"invalid_field": "invalid_value"}
        response = client.post(
            "/v1/generate",
            data=json.dumps(request_data),
            content_type="application/json",
            headers={"X-API-Key": self.TEST_API_KEY},
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "Invalid request data" in data["error"]

    def test_generate_script_missing_required_fields(self, client):
        """Test generation with missing required installer metadata fields."""
        request_data = {
            "installer_metadata": {
                "name": "Test App",
                "version": "1.0.0",
            }
        }
        response = client.post(
            "/v1/generate",
            data=json.dumps(request_data),
            content_type="application/json",
            headers={"X-API-Key": self.TEST_API_KEY},
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "Missing required installer metadata fields" in data["error"]

    @patch("ai_psadt_agent.api.routes.generation.get_script_generator")
    def test_generate_script_with_api_key_auth_variants(
        self,
        mock_get_generator,
        client,  # Original client fixture
        sample_installer_metadata,
        sample_generation_result,
    ):
        """Test script generation with API key authentication (variants)."""
        mock_generator = Mock()
        mock_generator.generate_script.return_value = sample_generation_result
        mock_get_generator.return_value = mock_generator
        request_data = {"installer_metadata": sample_installer_metadata, "save_to_package": False}

        # Test with correct X-API-Key
        with patch.dict("os.environ", {"API_KEY": "specific-test-key-for-variants"}):
            # Create a new app and client within this context to pick up the new API_KEY
            # This is important because the app fixture `client` is function-scoped and
            # would have been created with the os.environ state at the start of the test function.
            # We need a client that sees the API_KEY we just set.

            # Re-create app and client for this specific os.environ context
            # Note: This assumes create_app() reads os.environ["API_KEY"] at instantiation time.
            # If get_api_key() is called dynamically per request, this re-creation might not be strictly needed,
            # but it's safer for ensuring the test environment is as expected.

            # For this test, we'll use the existing `client` but ensure the `require_api_key` decorator
            # inside the app sees the patched os.environ. This should work if `get_api_key()` is called per request.

            response_x_api_key = client.post(
                "/v1/generate",
                data=json.dumps(request_data),
                content_type="application/json",
                headers={"X-API-Key": "specific-test-key-for-variants"},
            )
            assert response_x_api_key.status_code == 200

            # Test with correct Authorization Bearer token
            response_bearer = client.post(
                "/v1/generate",
                data=json.dumps(request_data),
                content_type="application/json",
                headers={"Authorization": "Bearer specific-test-key-for-variants"},
            )
            assert response_bearer.status_code == 200

            # Test without API key (should fail if API_KEY is configured)
            response_no_key = client.post(
                "/v1/generate", data=json.dumps(request_data), content_type="application/json"
            )
            assert response_no_key.status_code == 401
            assert "API key required" in json.loads(response_no_key.data)["error"]

            # Test with incorrect API key
            response_wrong_key = client.post(
                "/v1/generate",
                data=json.dumps(request_data),
                content_type="application/json",
                headers={"X-API-Key": "wrong-key-for-variants"},
            )
            assert response_wrong_key.status_code == 401
            assert "Invalid API key" in json.loads(response_wrong_key.data)["error"]

        # Test with no API_KEY configured in env (should allow access)
        with patch.dict("os.environ", {"API_KEY": ""}):
            # Create a new app and client to ensure it picks up the cleared API_KEY
            no_key_app = create_app()
            no_key_app.config["TESTING"] = True
            no_key_client = no_key_app.test_client()

            response_no_env_key = no_key_client.post(
                "/v1/generate", data=json.dumps(request_data), content_type="application/json"
            )
            # This assertion depends on how require_api_key handles an empty configured API_KEY.
            # Based on auth.py, if configured_api_key is empty, it allows access.
            assert response_no_env_key.status_code == 200

    @patch("ai_psadt_agent.api.routes.generation.get_script_generator")
    def test_generate_script_error_handling(self, mock_get_generator, client, sample_installer_metadata):
        """Test error handling in script generation."""
        mock_generator = Mock()
        mock_generator.generate_script.side_effect = Exception("LLM service unavailable")
        mock_get_generator.return_value = mock_generator
        request_data = {"installer_metadata": sample_installer_metadata, "save_to_package": False}

        response = client.post(
            "/v1/generate",
            data=json.dumps(request_data),
            content_type="application/json",
            headers={"X-API-Key": self.TEST_API_KEY},
        )
        assert response.status_code == 500
        data = json.loads(response.data)
        assert "error" in data
        assert "Script generation failed" in data["error"]

    @patch("ai_psadt_agent.api.routes.generation.get_script_generator")
    def test_validate_script_success(self, mock_get_generator, client):
        """Test successful script validation."""
        mock_generator = Mock()
        mock_linter = Mock()
        mock_linter.validate_script.return_value = {
            "valid": True,
            "score": 90,
            "issues": [],
            "suggestions": ["Consider adding more comments"],
        }
        mock_generator.compliance_linter = mock_linter
        mock_get_generator.return_value = mock_generator
        request_data = {"script_content": "Valid PSADT Script Content"}

        response = client.post(
            "/v1/validate",
            data=json.dumps(request_data),
            content_type="application/json",
            headers={"X-API-Key": self.TEST_API_KEY},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["valid"] is True

    def test_validate_script_missing_content(self, client):
        """Test validation with missing script content."""
        response = client.post(
            "/v1/validate",
            data=json.dumps({}),
            content_type="application/json",
            headers={"X-API-Key": self.TEST_API_KEY},
        )
        assert response.status_code == 400
        assert "script_content is required" in json.loads(response.data)["error"]

    def test_validate_script_empty_content(self, client):
        """Test validation with empty script content."""
        response = client.post(
            "/v1/validate",
            data=json.dumps({"script_content": "   "}),
            content_type="application/json",
            headers={"X-API-Key": self.TEST_API_KEY},
        )
        assert response.status_code == 400
        assert "script_content cannot be empty" in json.loads(response.data)["error"]

    @patch("ai_psadt_agent.api.routes.generation.get_script_generator")
    def test_generation_status_success(self, mock_get_generator, client):
        """Test generation status endpoint."""
        mock_generator = Mock()
        mock_llm = Mock()
        mock_llm.get_provider_name.return_value = "openai"
        mock_generator.llm_provider = mock_llm
        mock_get_generator.return_value = mock_generator

        response = client.get("/v1/status", headers={"X-API-Key": self.TEST_API_KEY})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["services"]["llm_provider"] == "openai"

    @patch("ai_psadt_agent.api.routes.generation.get_script_generator")
    def test_generation_status_error_handling(self, mock_get_generator, client):
        """Test generation status error handling."""
        mock_get_generator.side_effect = Exception("Service init failed")
        response = client.get("/v1/status", headers={"X-API-Key": self.TEST_API_KEY})
        assert response.status_code == 500
        assert "Status check failed" in json.loads(response.data)["error"]


class TestGenerationIntegration:
    """Integration tests for the complete generation pipeline."""

    TEST_API_KEY = "default-test-api-key"

    @patch("ai_psadt_agent.services.script_generator.get_llm_provider")
    def test_full_generation_pipeline(self, mock_llm_provider, client, sample_installer_metadata):
        """Test the complete generation pipeline from API to response."""
        mock_llm_instance = Mock()
        mock_llm_response_obj = Mock()  # Renamed to avoid conflict with LLMResponse model
        mock_llm_response_obj.content = "```powershell\nValid PSADT Script\n```"
        mock_llm_response_obj.model = "gpt-4o"
        mock_llm_response_obj.usage = {"total_tokens": 100}
        mock_llm_response_obj.tool_calls = None  # Ensure tool_calls is explicitly None
        mock_llm_instance.generate.return_value = mock_llm_response_obj
        mock_llm_provider.return_value = mock_llm_instance

        # Patch the linter within ScriptGenerator for this test
        with patch("ai_psadt_agent.services.script_generator.ComplianceLinter") as MockLinter:
            mock_linter_instance = MockLinter.return_value
            mock_linter_instance.validate_script.return_value = {
                "valid": True,
                "score": 95,
                "issues": [],
                "suggestions": [],
            }

            request_data = {
                "installer_metadata": sample_installer_metadata,
                "user_notes": "Silent install.",
                "save_to_package": False,
            }
            response = client.post(
                "/v1/generate",
                data=json.dumps(request_data),
                content_type="application/json",
                headers={"X-API-Key": self.TEST_API_KEY},
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert "Valid PSADT Script" in data["script_content"]
            assert data["validation_score"] == 95
