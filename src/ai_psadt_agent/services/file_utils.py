"""File utility functions for safe handling of uploaded files."""

import re
from pathlib import Path
from typing import Optional


def secure_filename(filename: Optional[str]) -> str:
    """
    Sanitize a filename for secure storage.

    - Removes or replaces dangerous characters
    - Prevents path traversal attacks
    - Ensures reasonable length limits
    - Handles edge cases like empty/None filenames

    Args:
        filename: The original filename to sanitize

    Returns:
        A safe filename string

    Examples:
        >>> secure_filename("../../../etc/passwd")
        'etc_passwd'
        >>> secure_filename("my file.exe")
        'my_file.exe'
        >>> secure_filename("")
        'unnamed_file'
    """
    if not filename or not filename.strip():
        return "unnamed_file"

    # Remove leading/trailing whitespace
    filename = filename.strip()

    # Replace path separators, spaces, and dangerous characters with underscore
    filename = re.sub(r'[/\\:*?"<>|\s]', "_", filename)

    # Remove any remaining path traversal attempts
    filename = re.sub(r"\.\.+", "", filename)

    # Remove leading dots and underscores
    filename = filename.lstrip("._")

    # Ensure reasonable length (max 100 chars, preserving extension if possible)
    if len(filename) > 100:
        name_part = Path(filename).stem[:90]
        ext_part = Path(filename).suffix[:10]
        filename = f"{name_part}{ext_part}"

    # Final fallback for empty result
    if not filename:
        return "unnamed_file"

    return filename


def get_upload_path(package_uuid: str, filename: str) -> Path:
    """
    Generate a secure upload path for a package file.

    Args:
        package_uuid: UUID of the package
        filename: Original filename (will be sanitized)

    Returns:
        Path object for the upload location
    """
    safe_filename = secure_filename(filename)
    upload_filename = f"{package_uuid}_{safe_filename}"
    return Path("instance/uploads") / upload_filename
