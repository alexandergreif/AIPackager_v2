"""Unit tests for domain models, including Pydantic model validation."""

import pytest
from ai_psadt_agent.domain_models.psadt_script import (
    Command,
    PSADTScript,
    Section,
)
from pydantic import ValidationError


class TestPSADTScriptModels:
    """Tests for PSADTScript related Pydantic models."""

    def test_command_creation_success(self):
        """Test successful creation of a Command model."""
        cmd_data = {
            "name": "Execute-Process",
            "parameters": {"Path": "setup.exe", "Parameters": "/S"},
            "comment": "Run the installer silently.",
        }
        command = Command(**cmd_data)
        assert command.name == "Execute-Process"
        assert command.parameters["Path"] == "setup.exe"
        assert command.comment == "Run the installer silently."

    def test_command_creation_missing_name_fails(self):
        """Test Command creation fails if 'name' is missing."""
        with pytest.raises(ValidationError):
            Command(parameters={})

    def test_section_creation_success(self):
        """Test successful creation of a Section model."""
        cmd_data = {"name": "Show-InstallationWelcome", "parameters": {}}
        section_data = {
            "name": "Installation",
            "commands": [cmd_data],
            "comment": "Main installation phase.",
        }
        section = Section(**section_data)
        assert section.name == "Installation"
        assert len(section.commands) == 1
        assert section.commands[0].name == "Show-InstallationWelcome"
        assert section.comment == "Main installation phase."

    def test_psadt_script_creation_success(self):
        """Test successful creation of a PSADTScript model."""
        install_section_data = {
            "name": "Installation",
            "commands": [{"name": "Execute-Process", "parameters": {"Path": "app.exe"}}],
        }
        script_data = {
            "variables": {"appName": "MyTestApp", "appVersion": "1.0"},
            "installation": install_section_data,
            "post_installation": {
                "name": "Post-Installation",
                "commands": [{"name": "Write-Log", "parameters": {"Message": "Done!"}}],
            },
        }
        psadt_script = PSADTScript(**script_data)
        assert psadt_script.variables["appName"] == "MyTestApp"
        assert psadt_script.installation.name == "Installation"
        assert len(psadt_script.installation.commands) == 1
        assert psadt_script.post_installation is not None
        assert psadt_script.post_installation.name == "Post-Installation"

    def test_psadt_script_missing_installation_section_fails(self):
        """Test PSADTScript creation fails if 'installation' section is missing."""
        with pytest.raises(ValidationError):
            PSADTScript(variables={"appName": "Test"})

    def test_psadt_script_from_simulated_llm_json(self):
        """Test parsing PSADTScript from a simulated LLM JSON output."""
        llm_json_output = {
            "variables": {
                "appVendor": "TestVendor",
                "appName": "TestApp",
                "appVersion": "1.2.3",
            },
            "custom_functions": ["Function Custom-Function {\nWrite-Host 'Hello'\n}"],
            "installation": {
                "name": "Installation",
                "commands": [
                    {
                        "name": "Show-InstallationWelcome",
                        "parameters": {"Message": "Welcome to TestApp installation."},
                    },
                    {
                        "name": "Execute-Process",
                        "parameters": {
                            "Path": "setup.exe",
                            "Parameters": "/silent /norestart",
                            "WaitForMsiExec": True,
                        },
                        "comment": "Run main installer.",
                    },
                ],
                "comment": "This is the main installation logic.",
            },
            "post_installation": {
                "name": "Post-Installation",
                "commands": [
                    {
                        "name": "Set-RegistryKey",
                        "parameters": {
                            "Path": "HKLM\\Software\\TestVendor\\TestApp",
                            "Name": "InstalledVersion",
                            "Value": "1.2.3",
                            "Type": "String",
                        },
                    }
                ],
            },
        }

        # This simulates json.loads(tool_call.function.arguments)
        # then PSADTScript(**tool_args)
        parsed_script = PSADTScript(**llm_json_output)

        assert parsed_script.variables["appVersion"] == "1.2.3"
        assert len(parsed_script.custom_functions) == 1
        assert "Custom-Function" in parsed_script.custom_functions[0]

        assert parsed_script.installation.name == "Installation"
        assert len(parsed_script.installation.commands) == 2
        assert parsed_script.installation.commands[1].name == "Execute-Process"
        assert parsed_script.installation.commands[1].parameters["WaitForMsiExec"] is True
        assert parsed_script.installation.comment == "This is the main installation logic."

        assert parsed_script.post_installation is not None
        assert parsed_script.post_installation.name == "Post-Installation"
        assert parsed_script.post_installation.commands[0].name == "Set-RegistryKey"

        assert parsed_script.pre_installation is None
        assert parsed_script.uninstallation is None
        assert parsed_script.pre_uninstallation is None
        assert parsed_script.post_uninstallation is None

    def test_psadt_script_extra_fields_fail(self):
        """Test that extra fields in PSADTScript cause validation error due to Config.extra = 'forbid'."""
        install_section_data = {"name": "Installation", "commands": []}
        script_data_with_extra = {
            "installation": install_section_data,
            "unexpected_field": "some_value",
        }
        with pytest.raises(ValidationError) as excinfo:
            PSADTScript(**script_data_with_extra)
        assert "unexpected_field" in str(excinfo.value)
        assert "Extra inputs are not permitted" in str(excinfo.value)
