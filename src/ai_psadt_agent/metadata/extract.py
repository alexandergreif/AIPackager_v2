"""Metadata extraction from installer files."""

import re
import subprocess
from pathlib import Path
from typing import Dict

from loguru import logger

from ..services.prompt_templates import InstallerMetadata


def extract_metadata(path: Path) -> InstallerMetadata:
    """
    Extract metadata from an installer file.

    Args:
        path: Path to the installer file

    Returns:
        InstallerMetadata object with extracted information

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file type is not supported
    """
    if not path.exists():
        raise FileNotFoundError(f"Installer file not found: {path}")

    file_extension = path.suffix.lower()

    if file_extension == ".msi":
        return _extract_msi_metadata(path)
    elif file_extension == ".exe":
        return _extract_exe_metadata(path)
    else:
        raise ValueError(f"Unsupported installer type: {file_extension}")


def _extract_msi_metadata(path: Path) -> InstallerMetadata:
    """
    Extract metadata from MSI files using lessmsi.

    Args:
        path: Path to the MSI file

    Returns:
        InstallerMetadata with extracted MSI properties
    """
    logger.info(f"Extracting MSI metadata from {path}")

    try:
        # Run lessmsi info command
        result = subprocess.run(["lessmsi", "info", str(path)], capture_output=True, text=True, timeout=30, check=True)

        # Parse the output
        properties = _parse_lessmsi_output(result.stdout)

        # Extract key properties
        product_name = properties.get("ProductName", path.stem)
        product_version = properties.get("ProductVersion", "1.0.0")

        # Determine architecture from MSI properties
        architecture = _determine_msi_architecture(properties)

        # MSI files typically support silent installation with /qn
        silent_args = "/qn /norestart"

        return InstallerMetadata(
            name=product_name,
            version=product_version,
            vendor=properties.get("Manufacturer", "Unknown"),
            installer_type="msi",
            architecture=architecture,
            silent_args=silent_args,
            language=properties.get("ProductLanguage", "EN"),
        )

    except subprocess.CalledProcessError as e:
        logger.warning(f"lessmsi failed for {path}: {e}")
        return _create_fallback_metadata(path, "msi")
    except subprocess.TimeoutExpired:
        logger.warning(f"lessmsi timed out for {path}")
        return _create_fallback_metadata(path, "msi")
    except FileNotFoundError:
        logger.warning("lessmsi not found, using fallback metadata extraction")
        return _create_fallback_metadata(path, "msi")


def _extract_exe_metadata(path: Path) -> InstallerMetadata:
    """
    Extract metadata from EXE files using header detection.

    Args:
        path: Path to the EXE file

    Returns:
        InstallerMetadata with detected installer type and default switches
    """
    logger.info(f"Extracting EXE metadata from {path}")

    try:
        # Read the first 1KB of the file to detect installer type
        with open(path, "rb") as f:
            header_data = f.read(1024)

        # Detect installer type based on header signatures
        installer_type = _detect_exe_installer_type(header_data, path.name)

        # Get default silent switches based on detected type
        silent_args = _get_default_silent_switches(installer_type)

        # Try to extract version from filename
        version = _extract_version_from_filename(path.name)

        return InstallerMetadata(
            name=_extract_name_from_filename(path.name),
            version=version,
            vendor="Unknown",
            installer_type="exe",
            architecture="x64",  # Default to x64 for modern installers
            silent_args=silent_args,
            language="EN",
        )

    except (OSError, IOError) as e:
        logger.warning(f"Failed to read EXE file {path}: {e}")
        return _create_fallback_metadata(path, "exe")


def _parse_lessmsi_output(output: str) -> Dict[str, str]:
    """
    Parse lessmsi info output into a properties dictionary.

    Args:
        output: Raw output from lessmsi info command

    Returns:
        Dictionary of MSI properties
    """
    properties = {}

    # lessmsi info output format is typically:
    # Property: Value
    for line in output.strip().split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            properties[key.strip()] = value.strip()

    return properties


def _determine_msi_architecture(properties: Dict[str, str]) -> str:
    """
    Determine architecture from MSI properties.

    Args:
        properties: Dictionary of MSI properties

    Returns:
        Architecture string ("x86" or "x64")
    """
    # Check common MSI properties that indicate architecture
    template = properties.get("Template", "")
    platform = properties.get("Platform", "")

    # Intel64 or x64 indicates 64-bit
    if any(arch in template.lower() for arch in ["intel64", "x64", "amd64"]):
        return "x64"

    if any(arch in platform.lower() for arch in ["x64", "amd64"]):
        return "x64"

    # Default to x86 if not clearly x64
    return "x86"


def _detect_exe_installer_type(header_data: bytes, filename: str) -> str:
    """
    Detect EXE installer type from header data and filename.

    Args:
        header_data: First 1KB of the EXE file
        filename: Name of the EXE file

    Returns:
        Detected installer type
    """
    header_str = header_data.decode("latin-1", errors="ignore").lower()
    filename_lower = filename.lower()

    # Inno Setup
    if "inno setup" in header_str or "innosetup" in filename_lower:
        return "inno"

    # NSIS
    if "nullsoft" in header_str or "nsis" in filename_lower:
        return "nsis"

    # InstallShield
    if "installshield" in header_str or "installshield" in filename_lower:
        return "installshield"

    # Advanced Installer
    if "advanced installer" in header_str:
        return "advanced_installer"

    # WiX Burn bundle
    if "burn" in header_str and "setup" in filename_lower:
        return "burn"

    # Generic setup
    if "setup" in filename_lower:
        return "generic_setup"

    # Default to generic
    return "generic"


def _get_default_silent_switches(installer_type: str) -> str:
    """
    Get default silent installation switches for different installer types.

    Args:
        installer_type: Detected installer type

    Returns:
        Default silent switches
    """
    switches_map = {
        "inno": "/SILENT /NORESTART",
        "nsis": "/S",
        "installshield": '/s /v"/qn"',
        "advanced_installer": "/quiet",
        "burn": "/quiet",
        "generic_setup": "/S",
        "generic": "/S",
    }

    return switches_map.get(installer_type, "/S")


def _extract_version_from_filename(filename: str) -> str:
    """
    Extract version number from filename using regex patterns.

    Args:
        filename: Name of the installer file

    Returns:
        Extracted version or default
    """
    # Common version patterns
    patterns = [
        r"v?(\d+\.\d+\.\d+\.\d+)",  # 1.2.3.4
        r"v?(\d+\.\d+\.\d+)",  # 1.2.3
        r"v?(\d+\.\d+)",  # 1.2
        r"_(\d+\.\d+\.\d+)_",  # _1.2.3_
        r"-(\d+\.\d+\.\d+)-",  # -1.2.3-
    ]

    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            return match.group(1)

    return "1.0.0"


def _extract_name_from_filename(filename: str) -> str:
    """
    Extract application name from filename.

    Args:
        filename: Name of the installer file

    Returns:
        Cleaned application name
    """
    # Remove file extension
    name = Path(filename).stem

    # First, remove version patterns (be more specific)
    name = re.sub(r"[_-]?v\d+[\d\._-]*", "", name, flags=re.IGNORECASE)
    name = re.sub(r"[_-]?\d+\.\d+[\d\._-]*", "", name, flags=re.IGNORECASE)

    # Remove common installer suffixes with underscore/dash boundaries
    suffixes_to_remove = ["setup", "installer", "install", "x64", "x86", "win64", "win32", "windows"]

    # Remove suffixes that are separated by underscores or dashes
    for suffix in suffixes_to_remove:
        # Remove suffix at end with separator
        name = re.sub(rf"[_-]{suffix}$", "", name, flags=re.IGNORECASE)
        # Remove suffix in middle with separators
        name = re.sub(rf"[_-]{suffix}[_-]", "_", name, flags=re.IGNORECASE)
        # Remove suffix at beginning with separator
        name = re.sub(rf"^{suffix}[_-]", "", name, flags=re.IGNORECASE)

    # Clean up separators and convert to proper case
    name = re.sub(r"[_-]+", " ", name).strip()
    name = " ".join(word.capitalize() for word in name.split() if word)

    return name if name else "Unknown Application"


def _create_fallback_metadata(path: Path, installer_type: str) -> InstallerMetadata:
    """
    Create fallback metadata when extraction fails.

    Args:
        path: Path to the installer file
        installer_type: Type of installer (msi/exe)

    Returns:
        Fallback InstallerMetadata
    """
    logger.info(f"Creating fallback metadata for {path}")

    if installer_type == "msi":
        silent_args = "/qn /norestart"
    else:
        silent_args = "/S"

    return InstallerMetadata(
        name=_extract_name_from_filename(path.name),
        version=_extract_version_from_filename(path.name),
        vendor="Unknown",
        installer_type=installer_type,
        architecture="x64",
        silent_args=silent_args,
        language="EN",
    )
