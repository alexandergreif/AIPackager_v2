"""Unit tests for file utility functions."""

from pathlib import Path

from ai_psadt_agent.services.file_utils import get_upload_path, secure_filename


class TestSecureFilename:
    """Test cases for secure_filename function."""

    def test_normal_filename(self) -> None:
        """Test normal filename remains unchanged."""
        result = secure_filename("document.pdf")
        assert result == "document.pdf"

    def test_filename_with_spaces(self) -> None:
        """Test filename with spaces gets underscores."""
        result = secure_filename("my file.exe")
        assert result == "my_file.exe"

    def test_path_traversal_attack(self) -> None:
        """Test path traversal attempts are sanitized."""
        result = secure_filename("../../../etc/passwd")
        assert result == "etc_passwd"

        result = secure_filename("..\\..\\windows\\system32\\config")
        assert result == "windows_system32_config"

    def test_dangerous_characters(self) -> None:
        """Test dangerous characters are replaced."""
        result = secure_filename('file<>:"|*?.exe')
        assert result == "file_______.exe"

    def test_empty_or_none_filename(self) -> None:
        """Test empty or None filenames return default."""
        assert secure_filename("") == "unnamed_file"
        assert secure_filename(None) == "unnamed_file"
        assert secure_filename("   ") == "unnamed_file"

    def test_leading_dots_and_underscores(self) -> None:
        """Test leading dots and underscores are removed."""
        result = secure_filename("...._hidden_file.txt")
        assert result == "hidden_file.txt"

    def test_multiple_consecutive_underscores(self) -> None:
        """Test multiple underscores are preserved."""
        result = secure_filename("file___with____many_underscores.txt")
        assert result == "file___with____many_underscores.txt"

    def test_long_filename_truncation(self) -> None:
        """Test very long filenames are truncated while preserving extension."""
        long_name = "a" * 150 + ".exe"
        result = secure_filename(long_name)

        # Should be truncated but still have .exe extension
        assert len(result) <= 100
        assert result.endswith(".exe")
        assert "a" in result

    def test_filename_with_only_extension(self) -> None:
        """Test filename that's only an extension."""
        result = secure_filename(".gitignore")
        assert result == "gitignore"

    def test_complex_malicious_filename(self) -> None:
        """Test complex malicious filename is properly sanitized."""
        malicious = "..\\..\\..\\<script>alert('xss')</script>|rm -rf /.exe"
        result = secure_filename(malicious)

        # Should be sanitized but still readable
        assert ".." not in result
        assert "\\" not in result
        assert "<" not in result
        assert ">" not in result
        assert "|" not in result
        assert result.endswith(".exe")


class TestGetUploadPath:
    """Test cases for get_upload_path function."""

    def test_normal_upload_path(self) -> None:
        """Test normal upload path generation."""
        uuid = "123e4567-e89b-12d3-a456-426614174000"
        filename = "installer.msi"

        result = get_upload_path(uuid, filename)
        expected = Path("instance/uploads") / f"{uuid}_installer.msi"

        assert result == expected

    def test_upload_path_with_unsafe_filename(self) -> None:
        """Test upload path with unsafe filename gets sanitized."""
        uuid = "123e4567-e89b-12d3-a456-426614174000"
        filename = "../../../malicious file.exe"

        result = get_upload_path(uuid, filename)
        expected = Path("instance/uploads") / f"{uuid}_malicious_file.exe"

        assert result == expected
        assert ".." not in str(result)

    def test_upload_path_components(self) -> None:
        """Test upload path has correct components."""
        uuid = "test-uuid"
        filename = "test.msi"

        result = get_upload_path(uuid, filename)

        # Should be under instance/uploads
        assert result.parts[0] == "instance"
        assert result.parts[1] == "uploads"

        # Filename should start with UUID
        assert result.name.startswith("test-uuid_")
        assert result.name.endswith("test.msi")
