"""Tests for AI generation services."""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import yaml
from ai_psadt_agent.services.knowledge_base import (
    Document,
    KnowledgeBase,
    SearchResult,
    initialize_knowledge_base,
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
from loguru import logger  # Added logger import


class TestLLMClient:
    """Test LLM client functionality."""

    def test_llm_message_creation(self):
        message = LLMMessage(role="user", content="Test message")
        assert message.role == "user"
        assert message.content == "Test message"

    def test_llm_response_creation(self):
        response = LLMResponse(content="Generated script", usage={"total_tokens": 100}, model="gpt-4o", tool_calls=None)
        assert response.content == "Generated script"
        assert response.usage is not None and response.usage["total_tokens"] == 100
        assert response.model == "gpt-4o"
        assert response.tool_calls is None

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("ai_psadt_agent.services.llm_client.openai.OpenAI")
    def test_openai_provider_initialization(self, mock_openai):
        provider = OpenAIProvider()
        assert provider.api_key == "test-key"
        assert provider.model == "gpt-4o"
        mock_openai.assert_called_once_with(api_key="test-key")

    def test_openai_provider_missing_key(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                OpenAIProvider()

    @patch.dict("os.environ", {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "test-key"})
    @patch("ai_psadt_agent.services.llm_client.OpenAIProvider")
    def test_get_llm_provider_factory(self, mock_provider):
        get_llm_provider()
        mock_provider.assert_called_once()


class TestKnowledgeBase:
    """Test knowledge base functionality."""

    def test_document_creation(self):
        doc = Document(id="test-doc", content="Test content", metadata={"filename": "test.md"})
        assert doc.id == "test-doc"

    def test_search_result_creation(self):
        doc = Document(id="test", content="content", metadata={})
        result = SearchResult(document=doc, score=0.85)
        assert result.document == doc

    @patch("ai_psadt_agent.services.knowledge_base.chromadb.PersistentClient")
    def test_knowledge_base_initialization_existing_collection(self, mock_client_constructor):
        mock_collection = Mock()
        mock_client_instance = mock_client_constructor.return_value
        mock_client_instance.get_collection.return_value = mock_collection

        kb = KnowledgeBase()
        assert kb.collection == mock_collection
        mock_client_instance.get_collection.assert_called_once_with(name="psadt_docs")
        mock_client_instance.create_collection.assert_not_called()

    @patch("ai_psadt_agent.services.knowledge_base.chromadb.PersistentClient")
    def test_knowledge_base_initialization_new_collection(self, mock_client_constructor):
        mock_collection = Mock()
        mock_client_instance = mock_client_constructor.return_value
        mock_client_instance.get_collection.side_effect = ValueError("Collection not found")
        mock_client_instance.create_collection.return_value = mock_collection

        kb = KnowledgeBase()
        assert kb.collection == mock_collection
        mock_client_instance.get_collection.assert_called_once_with(name="psadt_docs")
        mock_client_instance.create_collection.assert_called_once_with(
            name="psadt_docs", metadata={"description": "PSADT documentation for RAG"}
        )

    @patch("ai_psadt_agent.services.knowledge_base.chromadb.PersistentClient")
    def test_knowledge_base_add_document(self, mock_client_constructor):
        mock_collection = Mock()
        mock_client_instance = mock_client_constructor.return_value
        mock_client_instance.get_collection.side_effect = ValueError("not found")
        mock_client_instance.create_collection.return_value = mock_collection

        kb = KnowledgeBase()
        doc = Document(id="test", content="content", metadata={})
        kb.add_document(doc)
        mock_collection.add.assert_called_once_with(documents=["content"], ids=["test"], metadatas=[{}])

    @pytest.fixture
    def temp_switches_yaml(self, tmp_path: Path) -> Path:
        switches_content = {
            "TestApp1": [
                {
                    "installer_type": "msi",
                    "file_pattern": "testapp1*.msi",
                    "switches": "/qn /norestart",
                    "source": "test_fixture",
                }
            ],
            "TestApp2": {
                "installer_type": "exe",
                "file_pattern": "testapp2_setup.exe",
                "switches": "/S",
                "source": "test_fixture",
            },
            "Complex App Name": [
                {
                    "installer_type": "custom",
                    "file_pattern": "complex_app_installer.exe",
                    "switches": "--silent --agree",
                    "source": "test_fixture",
                }
            ],
        }
        yaml_file = tmp_path / "switches.yaml"
        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.dump(switches_content, f)
        return yaml_file

    @patch("ai_psadt_agent.services.knowledge_base.chromadb.PersistentClient")
    def test_load_switches_from_yaml(self, mock_persistent_client, temp_switches_yaml: Path):
        mock_collection = MagicMock()
        mock_client_instance = mock_persistent_client.return_value
        mock_client_instance.get_collection.side_effect = ValueError("Collection not found")
        mock_client_instance.create_collection.return_value = mock_collection

        kb = KnowledgeBase(persist_directory=str(temp_switches_yaml.parent / "chroma_test_load"))
        loaded_count = kb.load_switches_from_yaml(str(temp_switches_yaml))
        assert loaded_count == 3

        assert mock_collection.add.call_count > 0

        all_added_ids = []
        for call_args_obj in mock_collection.add.call_args_list:
            _, kwargs = call_args_obj
            all_added_ids.extend(kwargs.get("ids", []))

        assert "switch_testapp1_0" in all_added_ids
        assert "switch_testapp2_0" in all_added_ids
        assert "switch_complex_app_name_0" in all_added_ids

    @patch("ai_psadt_agent.services.knowledge_base.chromadb.PersistentClient")
    def test_find_switches_found(self, mock_persistent_client, temp_switches_yaml: Path):
        mock_collection = MagicMock()
        mock_client_instance = mock_persistent_client.return_value
        mock_client_instance.get_collection.side_effect = ValueError("not found")
        mock_client_instance.create_collection.return_value = mock_collection

        kb = KnowledgeBase(persist_directory=str(temp_switches_yaml.parent / "chroma_test_find"))

        test_app1_config = yaml.safe_load(temp_switches_yaml.read_text(encoding="utf-8"))["TestApp1"][0]
        doc_id_expected = "switch_testapp1_0"
        doc_content_expected = json.dumps(test_app1_config)
        doc_metadata_expected = {
            "type": "switch_config",
            "product_name": "TestApp1",
            "installer_type": "msi",
            "file_pattern": "testapp1*.msi",
            "source_file": "switches.yaml",
        }

        mock_collection.query.return_value = {
            "ids": [[doc_id_expected]],
            "documents": [[doc_content_expected]],
            "metadatas": [[doc_metadata_expected]],
            "distances": [[0.1]],
        }
        results = kb.find_switches(product_name="TestApp1")
        assert len(results) == 1
        assert results[0]["switches"] == "/qn /norestart"
        assert results[0]["_source_metadata"]["product_name"] == "TestApp1"

    @patch("ai_psadt_agent.services.knowledge_base.chromadb.PersistentClient")
    def test_find_switches_not_found(self, mock_persistent_client, temp_switches_yaml: Path):
        mock_collection = MagicMock()
        mock_client_instance = mock_persistent_client.return_value
        mock_client_instance.get_collection.side_effect = ValueError("not found")
        mock_client_instance.create_collection.return_value = mock_collection

        kb = KnowledgeBase(persist_directory=str(temp_switches_yaml.parent / "chroma_test_notfound"))
        mock_collection.query.return_value = {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        assert len(kb.find_switches(product_name="UnknownApp")) == 0

    @patch("ai_psadt_agent.services.knowledge_base.get_knowledge_base")
    def test_initialize_knowledge_base_loads_switches(self, mock_get_kb, tmp_path: Path):
        mock_kb_instance = MagicMock(spec=KnowledgeBase)
        mock_kb_instance.collection = MagicMock()
        mock_get_kb.return_value = mock_kb_instance

        mock_kb_instance.get_collection_count.return_value = 0
        mock_kb_instance.collection.get.return_value = {"ids": []}
        mock_kb_instance.index_directory.return_value = 5
        mock_kb_instance.load_switches_from_yaml.return_value = 3

        dummy_switches_file = tmp_path / "dummy_switches.yaml"
        dummy_switches_file.touch()
        dummy_docs_dir = tmp_path / "docs"
        dummy_docs_dir.mkdir()

        initialize_knowledge_base(docs_directory=str(dummy_docs_dir), switches_yaml_path_str=str(dummy_switches_file))

        mock_kb_instance.load_switches_from_yaml.assert_called_once_with(str(dummy_switches_file))
        mock_kb_instance.index_directory.assert_called_once_with(str(dummy_docs_dir))

    @pytest.fixture
    def initialized_kb(self, tmp_path: Path) -> KnowledgeBase:
        """Provides a KnowledgeBase instance initialized with actual project data paths."""
        # Create a temporary, isolated ChromaDB for this test to avoid conflicts/pollution
        # The persist_directory should be unique for this fixture.
        kb_persist_dir = tmp_path / "kb_fixture_chroma"
        kb_persist_dir.mkdir()

        # Point to the actual switches.yaml and docs directory
        # Assuming tests run from project root, and src is at project_root/src
        project_root = Path(__file__).parent.parent
        actual_switches_yaml = project_root / "src" / "ai_psadt_agent" / "resources" / "switches.yaml"
        actual_docs_dir = project_root / "docs" / "raw"

        # Ensure the actual switches.yaml exists for the test to be meaningful
        if not actual_switches_yaml.exists():
            pytest.skip(f"Actual switches.yaml not found at {actual_switches_yaml}, skipping test.")

        # Create a new KB instance for this test, pointing to the temp persist dir
        kb = KnowledgeBase(persist_directory=str(kb_persist_dir))
        # Manually load switches and index docs for this isolated KB instance
        kb.load_switches_from_yaml(str(actual_switches_yaml))
        if actual_docs_dir.exists():
            kb.index_directory(str(actual_docs_dir))
        else:
            logger.warning(f"Docs directory {actual_docs_dir} not found for initialized_kb fixture.")
        return kb

    def test_find_switches_for_fixture_apps(self, initialized_kb: KnowledgeBase):
        """Test find_switches for actual fixture apps from switches.yaml."""
        # Test for "7-Zip" which is in the example switches.yaml
        seven_zip_switches = initialized_kb.find_switches(product_name="7-Zip")
        assert seven_zip_switches, "Should find switches for 7-Zip"
        assert isinstance(seven_zip_switches, list)
        assert len(seven_zip_switches) > 0
        # Check some expected content (flexible check)
        found_msi_7zip = any(s.get("installer_type") == "msi" for s in seven_zip_switches)
        assert found_msi_7zip, "Should find MSI switches for 7-Zip"

        # Test for "Google Chrome"
        chrome_switches = initialized_kb.find_switches(product_name="Google Chrome")
        assert chrome_switches, "Should find switches for Google Chrome"
        assert len(chrome_switches) > 0
        found_msi_chrome = any(s.get("installer_type") == "msi" for s in chrome_switches)
        assert found_msi_chrome, "Should find MSI switches for Google Chrome"

        # Test for a specific exe name if available in switches.yaml
        # Example: Google Chrome with "ChromeSetup.exe"
        chrome_exe_switches = initialized_kb.find_switches(product_name="Google Chrome", exe_name="ChromeSetup.exe")
        assert chrome_exe_switches, "Should find switches for Google Chrome with exe_name ChromeSetup.exe"
        assert len(chrome_exe_switches) > 0
        assert chrome_exe_switches[0].get("installer_type") == "exe"


class TestPromptTemplates:
    """Test prompt template functionality."""

    def test_installer_metadata_creation(self):
        metadata = InstallerMetadata(name="Test App", version="1.0.0", vendor="Test Vendor", installer_type="msi")
        assert metadata.name == "Test App" and metadata.architecture == "x64"

    def test_prompt_builder_initialization(self):
        builder = PromptBuilder()
        assert "PSADT" in builder.system_prompt

    def test_build_generation_prompt(self):
        builder = PromptBuilder()
        metadata = InstallerMetadata(name="Test App", version="1.0.0", vendor="Test Vendor", installer_type="msi")
        messages = builder.build_generation_prompt(metadata)
        assert len(messages) == 2 and "Test App" in messages[1]["content"]

    def test_build_rag_query(self):
        metadata = InstallerMetadata(name="Microsoft Office", version="2021", vendor="Microsoft", installer_type="msi")
        query = build_rag_query(metadata, "silent installation")
        assert all(k in query for k in ["MSI", "Microsoft Office", "silent installation", "PSADT"])


class TestComplianceLinter:
    """Test compliance linter functionality."""

    def test_validate_good_script(self):
        linter = ComplianceLinter()
        # Shortened good_script for E501
        good_script_parts = [
            "<# .SYNOPSIS test #>",
            "<# .DESCRIPTION test #>",
            "[CmdletBinding()] Param()",
            "Try {",
            "Set-ExecutionPolicy Bypass -Scope Process -Force",
            "$appVendor='V';$appName='N';$appVersion='1'",
            "Show-InstallationWelcome",
            "Show-InstallationProgress",
            "Execute-MSI -Action Install",
            "Write-Log 'ok'",
            "Exit-Script -ExitCode 0",
            "}",
            "Catch { Write-Log 'err'; Exit-Script 1 }",
            "##* VARIABLE DECLARATION *##",
            "##* INSTALLATION *##",
        ]
        good_script = "\n".join(good_script_parts * 3)  # Repeat to ensure length
        result = linter.validate_script(good_script)
        assert result["valid"] is True and result["score"] >= 50

    def test_validate_bad_script(self):
        linter = ComplianceLinter()
        result = linter.validate_script("Write-Host 'Hello'")
        assert result["valid"] is False and result["score"] < 50


class TestScriptGenerator:
    """Test script generator functionality."""

    @patch("ai_psadt_agent.services.script_generator.get_llm_provider")
    @patch("ai_psadt_agent.services.script_generator.initialize_knowledge_base")
    def test_script_generator_initialization(self, mock_kb, mock_llm):
        mock_llm.return_value = Mock()
        mock_kb.return_value = Mock()
        generator = ScriptGenerator()
        assert (
            generator.llm_provider
            and generator.knowledge_base
            and generator.prompt_builder
            and generator.compliance_linter
        )

    def test_extract_script_content_from_code_block(self):
        generator = ScriptGenerator.__new__(ScriptGenerator)
        llm_response = "```powershell\n# Test\nWrite-Host 'Hello'\n```"
        script = generator._extract_script_content(llm_response)
        assert "# Test" in script and "Write-Host" in script

    def test_extract_script_content_from_plain_text(self):
        generator = ScriptGenerator.__new__(ScriptGenerator)
        llm_response = "<# .SYNOPSIS #>\nWrite-Host 'Test'"
        script = generator._extract_script_content(llm_response)
        assert ".SYNOPSIS" in script

    @patch("ai_psadt_agent.services.script_generator.get_llm_provider")
    @patch("ai_psadt_agent.services.script_generator.initialize_knowledge_base")
    def test_generate_script_integration(self, mock_initialize_kb, mock_get_llm):
        mock_llm_instance = Mock()
        mock_get_llm.return_value = mock_llm_instance

        mock_kb_instance = Mock(spec=KnowledgeBase)
        mock_kb_instance.search.return_value = []
        mock_initialize_kb.return_value = mock_kb_instance

        mock_tool_function = Mock()
        mock_tool_function.name = "generate_psadt_script"
        # Shortened arguments for E501
        tool_args_dict = {
            "variables": {"appName": "Test App from Tool", "appVersion": "1.0.0"},
            "installation": {
                "name": "Installation",
                "commands": [{"name": "Execute-Process", "parameters": {"Path": "test_tool.msi"}}],
            },
        }
        mock_tool_function.arguments = json.dumps(tool_args_dict)
        mock_tool_call = Mock()
        mock_tool_call.function = mock_tool_function

        mock_llm_response_with_tool = Mock(spec=LLMResponse)
        mock_llm_response_with_tool.content = None
        mock_llm_response_with_tool.tool_calls = [mock_tool_call]
        mock_llm_response_with_tool.model = "gpt-4o-tool-call"
        mock_llm_response_with_tool.usage = {"total_tokens": 600}

        mock_llm_instance.generate.return_value = mock_llm_response_with_tool

        generator = ScriptGenerator()
        metadata = InstallerMetadata(name="Test App", version="1.0.0", vendor="Test Vendor", installer_type="msi")
        result = generator.generate_script(metadata)

        assert isinstance(result, GenerationResult)
        assert result.structured_script is not None
        assert result.structured_script.variables["appName"] == "Test App from Tool"
        assert "Structured PSADT Script generated for: Installation" in result.script_content
        assert result.metadata["llm_model"] == "gpt-4o-tool-call"

    @patch("ai_psadt_agent.services.script_generator.get_llm_provider")
    @patch("ai_psadt_agent.services.script_generator.initialize_knowledge_base")
    def test_generate_script_llm_fallback_no_tool_call(self, mock_initialize_kb, mock_get_llm):
        mock_llm_instance = Mock()
        mock_get_llm.return_value = mock_llm_instance

        mock_kb_instance = Mock(spec=KnowledgeBase)
        mock_kb_instance.search.return_value = []
        mock_initialize_kb.return_value = mock_kb_instance

        mock_response_no_tool = Mock(spec=LLMResponse)
        # Shortened content for E501
        mock_response_no_tool.content = "<# .SYNOPSIS Raw Script #>\n" + "Write-Host 'Raw'\n" * 5
        mock_response_no_tool.tool_calls = None
        mock_response_no_tool.model = "gpt-4o-no-tool"
        mock_response_no_tool.usage = {"total_tokens": 300}
        mock_llm_instance.generate.return_value = mock_response_no_tool

        generator = ScriptGenerator()
        metadata = InstallerMetadata(name="Fallback App", version="1.0", vendor="Fallback Vendor", installer_type="exe")
        result = generator.generate_script(metadata)

        assert isinstance(result, GenerationResult)
        assert result.structured_script is None
        assert "Raw Script" in result.script_content
        assert result.metadata["llm_model"] == "gpt-4o-no-tool"
