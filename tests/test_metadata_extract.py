"""Unit tests for metadata extraction functionality."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from ai_psadt_agent.metadata.extract import (
    _create_fallback_metadata,
    _detect_exe_installer_type,
    _determine_msi_architecture,
    _extract_name_from_filename,
    _extract_version_from_filename,
    _get_default_silent_switches,
    _parse_lessmsi_output,
    extract_metadata,
)
from ai_psadt_agent.services.prompt_templates import InstallerMetadata


class TestExtractMetadata:
    """Test cases for the main extract_metadata function."""

    def test_extract_metadata_nonexistent_file(self):
        """Test extract_metadata with nonexistent file."""
        nonexistent_path = Path("nonexistent_file.msi")

        with pytest.raises(FileNotFoundError, match="Installer file not found"):
            extract_metadata(nonexistent_path)

    def test_extract_metadata_unsupported_type(self, tmp_path):
        """Test extract_metadata with unsupported file type."""
        unsupported_file = tmp_path / "test.zip"
        unsupported_file.touch()

        with pytest.raises(ValueError, match="Unsupported installer type"):
            extract_metadata(unsupported_file)

    @patch("ai_psadt_agent.metadata.extract._extract_msi_metadata")
    def test_extract_metadata_msi_file(self, mock_extract_msi, tmp_path):
        """Test extract_metadata delegates to MSI handler for .msi files."""
        msi_file = tmp_path / "test.msi"
        msi_file.touch()

        expected_metadata = InstallerMetadata(
            name="Test App", version="1.0.0", vendor="Test Corp", installer_type="msi"
        )
        mock_extract_msi.return_value = expected_metadata

        result = extract_metadata(msi_file)

        mock_extract_msi.assert_called_once_with(msi_file)
        assert result == expected_metadata

    @patch("ai_psadt_agent.metadata.extract._extract_exe_metadata")
    def test_extract_metadata_exe_file(self, mock_extract_exe, tmp_path):
        """Test extract_metadata delegates to EXE handler for .exe files."""
        exe_file = tmp_path / "test.exe"
        exe_file.touch()

        expected_metadata = InstallerMetadata(
            name="Test App", version="1.0.0", vendor="Test Corp", installer_type="exe"
        )
        mock_extract_exe.return_value = expected_metadata

        result = extract_metadata(exe_file)

        mock_extract_exe.assert_called_once_with(exe_file)
        assert result == expected_metadata


class TestMSIMetadataExtraction:
    """Test cases for MSI metadata extraction."""

    @patch("ai_psadt_agent.metadata.extract.subprocess.run")
    def test_msi_metadata_extraction_success(self, mock_subprocess, tmp_path):
        """Test successful MSI metadata extraction with lessmsi."""
        msi_file = tmp_path / "TestApp-1.2.3-x64.msi"
        msi_file.touch()

        # Mock lessmsi output
        mock_result = Mock()
        mock_result.stdout = """ProductName: Test Application
ProductVersion: 1.2.3.0
Manufacturer: Test Corporation
Template: Intel64;1033
ProductLanguage: 1033"""
        mock_subprocess.return_value = mock_result

        # Import the function to test
        from ai_psadt_agent.metadata.extract import _extract_msi_metadata

        result = _extract_msi_metadata(msi_file)

        assert result.name == "Test Application"
        assert result.version == "1.2.3.0"
        assert result.vendor == "Test Corporation"
        assert result.installer_type == "msi"
        assert result.architecture == "x64"
        assert result.silent_args == "/qn /norestart"

    @patch("ai_psadt_agent.metadata.extract.subprocess.run")
    def test_msi_metadata_extraction_lessmsi_failure(self, mock_subprocess, tmp_path):
        """Test MSI metadata extraction when lessmsi fails."""
        msi_file = tmp_path / "TestApp.msi"
        msi_file.touch()

        # Mock lessmsi failure
        mock_subprocess.side_effect = FileNotFoundError("lessmsi not found")

        from ai_psadt_agent.metadata.extract import _extract_msi_metadata

        result = _extract_msi_metadata(msi_file)

        # Should fall back to filename parsing
        assert result.name == "Testapp"
        assert result.installer_type == "msi"
        assert result.vendor == "Unknown"
        assert result.silent_args == "/qn /norestart"

    def test_parse_lessmsi_output(self):
        """Test parsing of lessmsi output."""
        output = """ProductName: Microsoft Office
ProductVersion: 16.0.14026.20334
Manufacturer: Microsoft Corporation
Template: Intel64;1033
Platform: x64"""

        properties = _parse_lessmsi_output(output)

        assert properties["ProductName"] == "Microsoft Office"
        assert properties["ProductVersion"] == "16.0.14026.20334"
        assert properties["Manufacturer"] == "Microsoft Corporation"
        assert properties["Template"] == "Intel64;1033"
        assert properties["Platform"] == "x64"

    def test_determine_msi_architecture_x64(self):
        """Test architecture determination for 64-bit MSI."""
        properties_intel64 = {"Template": "Intel64;1033"}
        assert _determine_msi_architecture(properties_intel64) == "x64"

        properties_x64 = {"Platform": "x64"}
        assert _determine_msi_architecture(properties_x64) == "x64"

        properties_amd64 = {"Template": "AMD64;1033"}
        assert _determine_msi_architecture(properties_amd64) == "x64"

    def test_determine_msi_architecture_x86(self):
        """Test architecture determination for 32-bit MSI."""
        properties_x86 = {"Template": "Intel;1033"}
        assert _determine_msi_architecture(properties_x86) == "x86"

        properties_empty = {}
        assert _determine_msi_architecture(properties_empty) == "x86"


class TestEXEMetadataExtraction:
    """Test cases for EXE metadata extraction."""

    def test_exe_metadata_extraction_inno_setup(self, tmp_path):
        """Test EXE metadata extraction for Inno Setup installer."""
        exe_file = tmp_path / "notepad++_setup_v8.4.6.exe"

        # Create fake EXE with Inno Setup signature
        with open(exe_file, "wb") as f:
            f.write(b"MZ" + b"\x00" * 100 + b"inno setup" + b"\x00" * 900)

        from ai_psadt_agent.metadata.extract import _extract_exe_metadata

        result = _extract_exe_metadata(exe_file)

        assert result.name == "Notepad++"
        assert result.version == "8.4.6"
        assert result.installer_type == "exe"
        assert result.silent_args == "/SILENT /NORESTART"
        assert result.architecture == "x64"

    def test_exe_metadata_extraction_nsis(self, tmp_path):
        """Test EXE metadata extraction for NSIS installer."""
        exe_file = tmp_path / "vlc-3.0.17-win64.exe"

        # Create fake EXE with NSIS signature
        with open(exe_file, "wb") as f:
            f.write(b"MZ" + b"\x00" * 100 + b"Nullsoft Install System" + b"\x00" * 800)

        from ai_psadt_agent.metadata.extract import _extract_exe_metadata

        result = _extract_exe_metadata(exe_file)

        assert result.name == "Vlcwin64"
        assert result.version == "3.0.17"
        assert result.installer_type == "exe"
        assert result.silent_args == "/S"

    def test_exe_metadata_extraction_file_read_error(self, tmp_path):
        """Test EXE metadata extraction when file cannot be read."""
        exe_file = tmp_path / "corrupted.exe"
        # Don't create the file to simulate read error

        from ai_psadt_agent.metadata.extract import _extract_exe_metadata

        result = _extract_exe_metadata(exe_file)

        # Should return fallback metadata
        assert result.name == "Corrupted"
        assert result.installer_type == "exe"
        assert result.vendor == "Unknown"

    def test_detect_exe_installer_type(self):
        """Test EXE installer type detection."""
        # Test Inno Setup detection
        inno_header = b"MZ\x00" * 50 + b"inno setup" + b"\x00" * 450
        assert _detect_exe_installer_type(inno_header, "setup.exe") == "inno"

        # Test NSIS detection
        nsis_header = b"MZ\x00" * 50 + b"nullsoft" + b"\x00" * 450
        assert _detect_exe_installer_type(nsis_header, "installer.exe") == "nsis"

        # Test InstallShield detection
        shield_header = b"MZ\x00" * 50 + b"installshield" + b"\x00" * 450
        assert _detect_exe_installer_type(shield_header, "setup.exe") == "installshield"

        # Test generic setup detection
        generic_header = b"MZ\x00" * 512
        assert _detect_exe_installer_type(generic_header, "setup.exe") == "generic_setup"

        # Test generic fallback
        assert _detect_exe_installer_type(generic_header, "app.exe") == "generic"

    def test_get_default_silent_switches(self):
        """Test default silent switches for different installer types."""
        assert _get_default_silent_switches("inno") == "/SILENT /NORESTART"
        assert _get_default_silent_switches("nsis") == "/S"
        assert _get_default_silent_switches("installshield") == '/s /v"/qn"'
        assert _get_default_silent_switches("advanced_installer") == "/quiet"
        assert _get_default_silent_switches("burn") == "/quiet"
        assert _get_default_silent_switches("generic_setup") == "/S"
        assert _get_default_silent_switches("generic") == "/S"
        assert _get_default_silent_switches("unknown_type") == "/S"


class TestUtilityFunctions:
    """Test cases for utility functions."""

    def test_extract_version_from_filename(self):
        """Test version extraction from various filename patterns."""
        assert _extract_version_from_filename("app-1.2.3.4-setup.exe") == "1.2.3.4"
        assert _extract_version_from_filename("installer_v2.1.0_x64.exe") == "2.1.0"
        assert _extract_version_from_filename("setup-3.14-win64.msi") == "3.14"
        assert _extract_version_from_filename("notepad_8.4.6_installer.exe") == "8.4.6"
        assert _extract_version_from_filename("app-without-version.exe") == "1.0.0"
        assert _extract_version_from_filename("v1.5.0-beta.exe") == "1.5.0"

    def test_extract_name_from_filename(self):
        """Test application name extraction from filenames."""
        assert _extract_name_from_filename("notepad-plus-plus-setup.exe") == "Notepad Plus Plus"
        assert _extract_name_from_filename("7zip_installer_v21.07_x64.msi") == "7zip Installerx64"
        assert _extract_name_from_filename("GoogleChrome-Setup.exe") == "Googlechrome"
        assert _extract_name_from_filename("vlc-3.0.17-win64-installer.exe") == "Vlcwin64"
        assert _extract_name_from_filename("app_v1.2.3_setup_x64.exe") == "Appsetup"
        assert _extract_name_from_filename("___--.exe") == "Unknown Application"

    def test_create_fallback_metadata(self, tmp_path):
        """Test fallback metadata creation."""
        msi_file = tmp_path / "TestApp_v2.1.0_x64.msi"
        exe_file = tmp_path / "AnotherApp-Setup-1.5.exe"

        msi_metadata = _create_fallback_metadata(msi_file, "msi")
        assert msi_metadata.name == "Testappx64"
        assert msi_metadata.version == "2.1.0"
        assert msi_metadata.installer_type == "msi"
        assert msi_metadata.silent_args == "/qn /norestart"
        assert msi_metadata.vendor == "Unknown"

        exe_metadata = _create_fallback_metadata(exe_file, "exe")
        assert exe_metadata.name == "Anotherapp"
        assert exe_metadata.version == "1.5"
        assert exe_metadata.installer_type == "exe"
        assert exe_metadata.silent_args == "/S"
        assert exe_metadata.vendor == "Unknown"


class TestIntegrationScenarios:
    """Integration test scenarios with sample files."""

    def test_msi_file_integration_with_mock_lessmsi(self, tmp_path):
        """Test full MSI extraction pipeline with mocked lessmsi."""
        msi_file = tmp_path / "7zip_21.07_x64.msi"
        msi_file.touch()

        with patch("ai_psadt_agent.metadata.extract.subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.stdout = """ProductName: 7-Zip 21.07 (x64)
ProductVersion: 21.07.00.0
Manufacturer: Igor Pavlov
Template: x64;1033
ProductLanguage: 1033"""
            mock_run.return_value = mock_result

            result = extract_metadata(msi_file)

            assert result.name == "7-Zip 21.07 (x64)"
            assert result.version == "21.07.00.0"
            assert result.vendor == "Igor Pavlov"
            assert result.installer_type == "msi"
            assert result.architecture == "x64"
            assert result.silent_args == "/qn /norestart"

    def test_exe_file_integration_inno_setup(self, tmp_path):
        """Test full EXE extraction pipeline for Inno Setup."""
        exe_file = tmp_path / "notepadplusplus_installer_v8.4.6.exe"

        # Create EXE file with Inno Setup signature
        with open(exe_file, "wb") as f:
            header = b"MZ\x90\x00" + b"\x00" * 60
            header += b"This program was created with Inno Setup"
            header += b"\x00" * (1024 - len(header))
            f.write(header)

        result = extract_metadata(exe_file)

        assert result.name == "Notepadplusplus"
        assert result.version == "8.4.6"
        assert result.installer_type == "exe"
        assert result.silent_args == "/SILENT /NORESTART"
        assert result.architecture == "x64"
        assert result.vendor == "Unknown"

    def test_exe_file_integration_nsis(self, tmp_path):
        """Test full EXE extraction pipeline for NSIS."""
        exe_file = tmp_path / "vlc_media_player_3.0.17_setup.exe"

        # Create EXE file with NSIS signature
        with open(exe_file, "wb") as f:
            header = b"MZ\x90\x00" + b"\x00" * 60
            header += b"Nullsoft Install System v3.08"
            header += b"\x00" * (1024 - len(header))
            f.write(header)

        result = extract_metadata(exe_file)

        assert result.name == "Vlc Media Playersetup"
        assert result.version == "3.0.17"
        assert result.installer_type == "exe"
        assert result.silent_args == "/S"
        assert result.architecture == "x64"
