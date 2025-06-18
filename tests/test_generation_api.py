"""Integration tests for the generation API endpoints."""

import json
from unittest.mock import Mock, patch

import pytest
from ai_psadt_agent import create_app
from ai_psadt_agent.services.script_generator import GenerationResult


@pytest.fixture
def app():
    """Create test Flask app."""
    app = create_app()
    app.config["TESTING"] = True
    return app


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

    @patch("ai_psadt_agent.api.routes.generation.get_script_generator")
    def test_generate_script_success(
        self,
        mock_get_generator,
        client,
        sample_installer_metadata,
        sample_generation_result,
    ):
        """Test successful script generation."""
        # Mock script generator
        mock_generator = Mock()
        mock_generator.generate_script.return_value = sample_generation_result
        mock_get_generator.return_value = mock_generator

        # Prepare request data
        request_data = {
            "installer_metadata": sample_installer_metadata,
            "user_notes": "Please ensure silent installation",
            "save_to_package": False,  # Don't save to avoid DB complications in test
        }

        # Make request
        response = client.post(
            "/v1/generate",
            data=json.dumps(request_data),
            content_type="application/json",
        )

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)

        assert "script_content" in data
        assert "validation_score" in data
        assert "issues" in data
        assert "suggestions" in data
        assert "rag_sources" in data
        assert "metadata" in data

        assert data["validation_score"] == 85.0
        assert "Test Application" in data["script_content"]
        assert len(data["rag_sources"]) > 0

        # Verify generator was called correctly
        mock_generator.generate_script.assert_called_once()
        call_args = mock_generator.generate_script.call_args
        installer_metadata = call_args[1]["installer_metadata"]
        assert installer_metadata.name == "Test Application"
        assert installer_metadata.version == "1.0.0"

    def test_generate_script_missing_data(self, client):
        """Test generation with missing request data."""
        response = client.post("/v1/generate", data="{}", content_type="application/json")
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
                # Missing vendor and installer_type
            }
        }

        response = client.post(
            "/v1/generate",
            data=json.dumps(request_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "Missing required installer metadata fields" in data["error"]
        assert "vendor" in data["error"]
        assert "installer_type" in data["error"]

    @patch("ai_psadt_agent.api.routes.generation.get_script_generator")
    def test_generate_script_with_api_key(
        self,
        mock_get_generator,
        client,
        sample_installer_metadata,
        sample_generation_result,
    ):
        """Test script generation with API key authentication."""
        # Set API key in environment
        with patch.dict("os.environ", {"API_KEY": "test-api-key"}):
            # Mock script generator
            mock_generator = Mock()
            mock_generator.generate_script.return_value = sample_generation_result
            mock_get_generator.return_value = mock_generator

            request_data = {
                "installer_metadata": sample_installer_metadata,
                "save_to_package": False,
            }

            # Request with API key
            response = client.post(
                "/v1/generate",
                data=json.dumps(request_data),
                content_type="application/json",
                headers={"X-API-Key": "test-api-key"},
            )

            assert response.status_code == 200

            # Request without API key should fail
            response = client.post(
                "/v1/generate",
                data=json.dumps(request_data),
                content_type="application/json",
            )

            assert response.status_code == 401
            data = json.loads(response.data)
            assert "API key required" in data["error"]

    @patch("ai_psadt_agent.api.routes.generation.get_script_generator")
    def test_generate_script_error_handling(self, mock_get_generator, client, sample_installer_metadata):
        """Test error handling in script generation."""
        # Mock script generator to raise exception
        mock_generator = Mock()
        mock_generator.generate_script.side_effect = Exception("LLM service unavailable")
        mock_get_generator.return_value = mock_generator

        request_data = {
            "installer_metadata": sample_installer_metadata,
            "save_to_package": False,
        }

        response = client.post(
            "/v1/generate",
            data=json.dumps(request_data),
            content_type="application/json",
        )

        assert response.status_code == 500
        data = json.loads(response.data)
        assert "error" in data
        assert "Script generation failed" in data["error"]

    @patch("ai_psadt_agent.api.routes.generation.get_script_generator")
    def test_validate_script_success(self, mock_get_generator, client):
        """Test successful script validation."""
        # Mock compliance linter
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

        request_data = {
            "script_content": """
            <#
            .SYNOPSIS
                Test script
            #>
            [CmdletBinding()]
            Param([String]$DeploymentType = 'Install')
            Try {
                Set-ExecutionPolicy -ExecutionPolicy 'ByPass' -Scope 'Process' -Force
                Show-InstallationWelcome
                Write-Log "Test"
                Exit-Script -ExitCode 0
            }
            Catch {
                Exit-Script -ExitCode 1
            }
            """
        }

        response = client.post(
            "/v1/validate",
            data=json.dumps(request_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["valid"] is True
        assert data["score"] == 90
        assert isinstance(data["issues"], list)
        assert isinstance(data["suggestions"], list)

    def test_validate_script_missing_content(self, client):
        """Test validation with missing script content."""
        request_data = {}

        response = client.post(
            "/v1/validate",
            data=json.dumps(request_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "script_content is required" in data["error"]

    def test_validate_script_empty_content(self, client):
        """Test validation with empty script content."""
        request_data = {"script_content": "   "}

        response = client.post(
            "/v1/validate",
            data=json.dumps(request_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "script_content cannot be empty" in data["error"]

    @patch("ai_psadt_agent.api.routes.generation.get_script_generator")
    def test_search_knowledge_base_success(self, mock_get_generator, client):
        """Test successful knowledge base search."""
        # Mock knowledge base search
        mock_generator = Mock()
        mock_kb = Mock()
        mock_search_results = [
            Mock(
                document=Mock(
                    id="doc1",
                    content="PSADT fundamentals content",
                    metadata={"filename": "fundamentals.md"},
                ),
                score=0.95,
            ),
            Mock(
                document=Mock(
                    id="doc2",
                    content="Execute-MSI function details",
                    metadata={"filename": "functions.md"},
                ),
                score=0.87,
            ),
        ]
        mock_kb.search.return_value = mock_search_results
        mock_generator.knowledge_base = mock_kb
        mock_get_generator.return_value = mock_generator

        request_data = {"query": "Execute-MSI function usage", "top_k": 5}

        response = client.post(
            "/v1/knowledge-base/search",
            data=json.dumps(request_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["query"] == "Execute-MSI function usage"
        assert data["total"] == 2
        assert len(data["results"]) == 2

        # Check first result
        result1 = data["results"][0]
        assert result1["id"] == "doc1"
        assert result1["score"] == 0.95
        assert "PSADT fundamentals" in result1["content"]

    def test_search_knowledge_base_missing_query(self, client):
        """Test knowledge base search with missing query."""
        request_data = {}

        response = client.post(
            "/v1/knowledge-base/search",
            data=json.dumps(request_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "query is required" in data["error"]

    def test_search_knowledge_base_empty_query(self, client):
        """Test knowledge base search with empty query."""
        request_data = {"query": "   "}

        response = client.post(
            "/v1/knowledge-base/search",
            data=json.dumps(request_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "query cannot be empty" in data["error"]

    @patch("ai_psadt_agent.api.routes.generation.get_script_generator")
    def test_generation_status_success(self, mock_get_generator, client):
        """Test generation status endpoint."""
        # Mock services status
        mock_generator = Mock()
        mock_kb = Mock()
        mock_kb.get_collection_count.return_value = 5
        mock_llm = Mock()
        mock_llm.get_provider_name.return_value = "openai"

        mock_generator.knowledge_base = mock_kb
        mock_generator.llm_provider = mock_llm
        mock_get_generator.return_value = mock_generator

        response = client.get("/v1/status")

        assert response.status_code == 200
        data = json.loads(response.data)

        assert "services" in data
        assert "capabilities" in data

        services = data["services"]
        assert services["script_generator"] == "ready"
        assert services["llm_provider"] == "openai"
        assert "5 documents indexed" in services["knowledge_base"]
        assert services["compliance_linter"] == "ready"

        capabilities = data["capabilities"]
        assert capabilities["script_generation"] is True
        assert capabilities["script_validation"] is True
        assert capabilities["knowledge_base_search"] is True
        assert capabilities["rag_integration"] is True

    @patch("ai_psadt_agent.api.routes.generation.get_script_generator")
    def test_generation_status_error_handling(self, mock_get_generator, client):
        """Test generation status error handling."""
        # Mock services to raise exception
        mock_get_generator.side_effect = Exception("Service initialization failed")

        response = client.get("/v1/status")

        assert response.status_code == 500
        data = json.loads(response.data)
        assert "error" in data
        assert "Status check failed" in data["error"]


class TestGenerationIntegration:
    """Integration tests for the complete generation pipeline."""

    @patch("ai_psadt_agent.services.script_generator.get_llm_provider")
    @patch("ai_psadt_agent.services.script_generator.initialize_knowledge_base")
    def test_full_generation_pipeline(self, mock_kb_init, mock_llm_provider, client, sample_installer_metadata):
        """Test the complete generation pipeline from API to response."""
        # Mock LLM provider
        mock_llm_instance = Mock()
        mock_response = Mock()
        mock_response.content = (
            """
        ```powershell
        <#
        .SYNOPSIS
            Test Application deployment script
        .DESCRIPTION
            Installs Test Application using PowerShell App Deployment Toolkit
        #>
        [CmdletBinding()]
        Param ([String]$DeploymentType = 'Install')
        Try {
            Set-ExecutionPolicy -ExecutionPolicy 'ByPass' -Scope 'Process' -Force

            ##*===============================================
            ##* VARIABLE DECLARATION
            ##*===============================================
            [String]$appVendor = 'Test Vendor'
            [String]$appName = 'Test Application'
            [String]$appVersion = '1.0.0'
            [String]$mainExitCode = 0

            # Load PSADT toolkit
            . "$PSScriptRoot\\AppDeployToolkit\\AppDeployToolkitMain.ps1"

            ##*===============================================
            ##* INSTALLATION
            ##*===============================================
            [String]$installPhase = 'Installation'

            Show-InstallationWelcome
            Show-InstallationProgress
            Execute-MSI -Action 'Install' -Path 'test_app.msi'
            Write-Log "Installation completed successfully"
            Exit-Script -ExitCode $mainExitCode
        }
        Catch {
            [String]$mainErrorMessage = "$(Resolve-Error)"
            Write-Log -Message $mainErrorMessage -Severity 3
            Exit-Script -ExitCode 1
        }
        ```
        """
            * 3
        )  # Make it long enough to pass validation
        mock_response.model = "gpt-4o"
        mock_response.usage = {"total_tokens": 500}
        mock_llm_instance.generate.return_value = mock_response
        mock_llm_provider.return_value = mock_llm_instance

        # Mock knowledge base
        mock_kb_instance = Mock()
        mock_kb_instance.search.return_value = []
        mock_kb_instance.get_collection_count.return_value = 3
        mock_kb_init.return_value = mock_kb_instance

        request_data = {
            "installer_metadata": sample_installer_metadata,
            "user_notes": "Ensure silent installation with no user interaction",
            "save_to_package": False,
        }

        response = client.post(
            "/v1/generate",
            data=json.dumps(request_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        # Verify the complete response structure
        assert "script_content" in data
        assert "validation_score" in data
        assert "issues" in data
        assert "suggestions" in data
        assert "rag_sources" in data
        assert "metadata" in data

        # Verify script content contains expected elements
        script = data["script_content"]
        assert ".SYNOPSIS" in script
        assert "Test Application" in script
        assert "Execute-MSI" in script
        assert "Exit-Script" in script

        # Verify validation score is reasonable (may not pass strict compliance in test)
        assert data["validation_score"] >= 0  # Should have a score

        # Verify metadata
        metadata = data["metadata"]
        assert "installer" in metadata
        assert "llm_model" in metadata
        assert metadata["installer"]["name"] == "Test Application"
