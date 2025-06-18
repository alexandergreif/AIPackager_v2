"""Tests for AI generation services."""

from unittest.mock import Mock, patch

import pytest
from ai_psadt_agent.services.knowledge_base import (
    Document,
    KnowledgeBase,
    SearchResult,
)
from ai_psadt_agent.services.llm_client import (
    LLMMessage,
    LLMResponse,
    OpenAIProvider,
    get_llm_provider,
)
from ai_psadt_agent.services.prompt_templates import (
    InstallerMetadata,
    PromptBuilder,
    build_rag_query,
)
from ai_psadt_agent.services.script_generator import (
    ComplianceLinter,
    GenerationResult,
    ScriptGenerator,
)


class TestLLMClient:
    """Test LLM client functionality."""

    def test_llm_message_creation(self):
        """Test LLM message creation."""
        message = LLMMessage(role="user", content="Test message")
        assert message.role == "user"
        assert message.content == "Test message"

    def test_llm_response_creation(self):
        """Test LLM response creation."""
        response = LLMResponse(content="Generated script", usage={"total_tokens": 100}, model="gpt-4o")
        assert response.content == "Generated script"
        assert response.usage["total_tokens"] == 100
        assert response.model == "gpt-4o"

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("ai_psadt_agent.services.llm_client.openai.OpenAI")
    def test_openai_provider_initialization(self, mock_openai):
        """Test OpenAI provider initialization."""
        provider = OpenAIProvider()
        assert provider.api_key == "test-key"
        assert provider.model == "gpt-4o"
        mock_openai.assert_called_once_with(api_key="test-key")

    def test_openai_provider_missing_key(self):
        """Test OpenAI provider fails without API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                OpenAIProvider()

    @patch.dict("os.environ", {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "test-key"})
    @patch("ai_psadt_agent.services.llm_client.OpenAIProvider")
    def test_get_llm_provider_factory(self, mock_provider):
        """Test LLM provider factory function."""
        get_llm_provider()
        mock_provider.assert_called_once()


class TestKnowledgeBase:
    """Test knowledge base functionality."""

    def test_document_creation(self):
        """Test document creation."""
        doc = Document(id="test-doc", content="Test content", metadata={"filename": "test.md"})
        assert doc.id == "test-doc"
        assert doc.content == "Test content"
        assert doc.metadata["filename"] == "test.md"

    def test_search_result_creation(self):
        """Test search result creation."""
        doc = Document(id="test", content="content", metadata={})
        result = SearchResult(document=doc, score=0.85)
        assert result.document == doc
        assert result.score == 0.85

    @patch("ai_psadt_agent.services.knowledge_base.chromadb.PersistentClient")
    def test_knowledge_base_initialization(self, mock_client):
        """Test knowledge base initialization."""
        mock_collection = Mock()
        mock_client.return_value.get_collection.return_value = mock_collection

        kb = KnowledgeBase()
        assert kb.collection_name == "psadt_docs"
        assert kb.persist_directory == "./chroma_db"

    @patch("ai_psadt_agent.services.knowledge_base.chromadb.PersistentClient")
    def test_knowledge_base_add_document(self, mock_client):
        """Test adding document to knowledge base."""
        mock_collection = Mock()
        mock_client.return_value.get_collection.return_value = mock_collection

        kb = KnowledgeBase()
        doc = Document(id="test", content="content", metadata={})

        kb.add_document(doc)
        mock_collection.add.assert_called_once_with(documents=["content"], ids=["test"], metadatas=[{}])


class TestPromptTemplates:
    """Test prompt template functionality."""

    def test_installer_metadata_creation(self):
        """Test installer metadata creation."""
        metadata = InstallerMetadata(name="Test App", version="1.0.0", vendor="Test Vendor", installer_type="msi")
        assert metadata.name == "Test App"
        assert metadata.version == "1.0.0"
        assert metadata.vendor == "Test Vendor"
        assert metadata.installer_type == "msi"
        assert metadata.architecture == "x64"  # default
        assert metadata.language == "EN"  # default

    def test_prompt_builder_initialization(self):
        """Test prompt builder initialization."""
        builder = PromptBuilder()
        assert builder.system_prompt is not None
        assert "PSADT" in builder.system_prompt

    def test_build_generation_prompt(self):
        """Test generation prompt building."""
        builder = PromptBuilder()
        metadata = InstallerMetadata(name="Test App", version="1.0.0", vendor="Test Vendor", installer_type="msi")

        messages = builder.build_generation_prompt(metadata)
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "Test App" in messages[1]["content"]

    def test_build_rag_query(self):
        """Test RAG query building."""
        metadata = InstallerMetadata(
            name="Microsoft Office",
            version="2021",
            vendor="Microsoft",
            installer_type="msi",
        )

        query = build_rag_query(metadata, "silent installation")
        assert "MSI" in query
        assert "Microsoft Office" in query
        assert "silent installation" in query
        assert "PSADT" in query


class TestComplianceLinter:
    """Test compliance linter functionality."""

    def test_compliance_linter_initialization(self):
        """Test compliance linter initialization."""
        linter = ComplianceLinter()
        assert len(linter.required_patterns) > 0
        assert len(linter.recommended_patterns) > 0
        assert len(linter.security_patterns) > 0

    def test_validate_good_script(self):
        """Test validation of a good PSADT script."""
        linter = ComplianceLinter()

        # Mock a good PSADT script that matches all required patterns
        good_script = (
            """
<#
.SYNOPSIS
    Test application deployment script
.DESCRIPTION
    Installs Test App using PowerShell App Deployment Toolkit
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
    [String]$appName = 'Test App'
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
    Execute-MSI -Action 'Install' -Path 'test.msi'
    Write-Log "Installation completed successfully"
    Exit-Script -ExitCode $mainExitCode
}
Catch {
    [String]$mainErrorMessage = "$(Resolve-Error)"
    Write-Log -Message $mainErrorMessage -Severity 3
    Exit-Script -ExitCode 1
}
"""
            * 3
        )  # Make it longer to pass length check

        result = linter.validate_script(good_script)
        assert result["valid"] is True
        assert result["score"] >= 70

    def test_validate_bad_script(self):
        """Test validation of a bad script."""
        linter = ComplianceLinter()

        # Very short, incomplete script
        bad_script = "Write-Host 'Hello World'"

        result = linter.validate_script(bad_script)
        assert result["valid"] is False
        assert result["score"] < 70
        assert len(result["issues"]) > 0


class TestScriptGenerator:
    """Test script generator functionality."""

    @patch("ai_psadt_agent.services.script_generator.get_llm_provider")
    @patch("ai_psadt_agent.services.script_generator.initialize_knowledge_base")
    def test_script_generator_initialization(self, mock_kb, mock_llm):
        """Test script generator initialization."""
        mock_llm.return_value = Mock()
        mock_kb.return_value = Mock()

        generator = ScriptGenerator()
        assert generator.llm_provider is not None
        assert generator.knowledge_base is not None
        assert generator.prompt_builder is not None
        assert generator.compliance_linter is not None

    def test_extract_script_content_from_code_block(self):
        """Test extracting script content from markdown code blocks."""
        generator = ScriptGenerator.__new__(ScriptGenerator)  # Create without __init__

        llm_response = """
        Here's your PSADT script:

        ```powershell
        # This is a test script
        Write-Host "Hello World"
        ```

        This script does XYZ.
        """

        script = generator._extract_script_content(llm_response)
        assert "# This is a test script" in script
        assert "Write-Host" in script
        assert "This script does XYZ" not in script

    def test_extract_script_content_from_plain_text(self):
        """Test extracting script content from plain text."""
        generator = ScriptGenerator.__new__(ScriptGenerator)  # Create without __init__

        llm_response = """
        <#
        .SYNOPSIS
            Test script
        #>

        Write-Host "Test"
        """

        script = generator._extract_script_content(llm_response)
        assert ".SYNOPSIS" in script
        assert "Write-Host" in script

    @patch("ai_psadt_agent.services.script_generator.get_llm_provider")
    @patch("ai_psadt_agent.services.script_generator.initialize_knowledge_base")
    def test_generate_script_integration(self, mock_kb, mock_llm):
        """Test script generation integration."""
        # Mock LLM provider
        mock_llm_instance = Mock()
        mock_response = Mock()
        mock_response.content = (
            """
        ```powershell
        <#
        .SYNOPSIS
            Test App deployment
        .DESCRIPTION
            Installs Test App
        #>
        [CmdletBinding()]
        Param ([String]$DeploymentType = 'Install')
        Try {
            Set-ExecutionPolicy -ExecutionPolicy 'ByPass' -Scope 'Process' -Force
            [String]$appVendor = 'Test Vendor'
            [String]$appName = 'Test App'
            [String]$appVersion = '1.0.0'
            ##*===============================================
            ##* VARIABLE DECLARATION
            ##*===============================================
            ##*===============================================
            ##* INSTALLATION
            ##*===============================================
            [String]$installPhase = 'Installation'
            Show-InstallationWelcome
            Show-InstallationProgress
            Execute-MSI -Action 'Install' -Path 'test.msi'
            Write-Log "Installation completed"
            Exit-Script -ExitCode 0
        }
        Catch {
            Write-Log "Error occurred"
            Exit-Script -ExitCode 1
        }
        ```
        """
            * 3
        )  # Make it long enough
        mock_response.model = "gpt-4o"
        mock_response.usage = {"total_tokens": 500}
        mock_llm_instance.generate.return_value = mock_response
        mock_llm.return_value = mock_llm_instance

        # Mock knowledge base
        mock_kb_instance = Mock()
        mock_kb_instance.search.return_value = []
        mock_kb.return_value = mock_kb_instance

        generator = ScriptGenerator()

        metadata = InstallerMetadata(name="Test App", version="1.0.0", vendor="Test Vendor", installer_type="msi")

        result = generator.generate_script(metadata)

        assert isinstance(result, GenerationResult)
        assert result.script_content is not None
        assert result.validation_score >= 0
        assert isinstance(result.issues, list)
        assert isinstance(result.suggestions, list)
