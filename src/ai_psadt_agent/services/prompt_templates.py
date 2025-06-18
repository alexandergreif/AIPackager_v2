"""Prompt templates for PSADT script generation with RAG integration."""

from dataclasses import dataclass
from typing import Dict, List, Optional

from .knowledge_base import SearchResult


@dataclass
class InstallerMetadata:
    """Metadata about the installer."""

    name: str
    version: str
    vendor: str
    installer_type: str  # "msi", "exe", "msp", etc.
    installer_path: Optional[str] = None
    silent_args: Optional[str] = None
    uninstall_args: Optional[str] = None
    architecture: str = "x64"
    language: str = "EN"
    notes: Optional[str] = None


class PromptBuilder:
    """Builder for PSADT script generation prompts."""

    def __init__(self) -> None:
        """Initialize the prompt builder."""
        self.system_prompt = self._get_system_prompt()

    def _get_system_prompt(self) -> str:
        """Get the system prompt for PSADT script generation."""
        return (
            "You are an expert PowerShell App Deployment Toolkit (PSADT) script generator.\n"
            "Your task is to create production-ready PSADT v3.9+ deployment scripts\n"
            "based on installer metadata and user requirements.\n\n"
            "Key Requirements:\n"
            "1. Generate complete, functional PSADT scripts following v3.9+ standards\n"
            "2. Use proper error handling with Try-Catch blocks\n"
            "3. Include appropriate logging with Write-Log\n"
            "4. Handle Install/Uninstall/Repair deployment types\n"
            "5. Use Show-InstallationWelcome and Show-InstallationProgress for user experience\n"
            "6. Follow PSADT best practices for enterprise deployment\n"
            "7. Include proper variable declarations and metadata\n"
            "8. Use Execute-MSI for MSI files, Execute-Process for EXE files\n"
            "9. Handle application closure gracefully\n"
            "10. Ensure clean exit with Exit-Script\n\n"
            "Always provide complete, working scripts that can be deployed immediately "
            "in enterprise environments."
        )

    def build_generation_prompt(
        self,
        installer_metadata: InstallerMetadata,
        user_notes: Optional[str] = None,
        rag_context: Optional[List[SearchResult]] = None,
    ) -> List[Dict[str, str]]:
        """Build the complete prompt for script generation.

        Args:
            installer_metadata: Metadata about the installer
            user_notes: Additional user requirements or notes
            rag_context: RAG search results for context

        Returns:
            List of messages for LLM
        """
        messages = [{"role": "system", "content": self.system_prompt}]

        # Build user prompt with installer metadata
        user_prompt = self._build_user_prompt(installer_metadata, user_notes, rag_context)
        messages.append({"role": "user", "content": user_prompt})

        return messages

    def _build_user_prompt(
        self,
        installer_metadata: InstallerMetadata,
        user_notes: Optional[str] = None,
        rag_context: Optional[List[SearchResult]] = None,
    ) -> str:
        """Build the user prompt with metadata and context.

        Args:
            installer_metadata: Installer metadata
            user_notes: User notes/requirements
            rag_context: RAG search results

        Returns:
            Formatted user prompt
        """
        prompt_parts = []

        # Add installer metadata
        prompt_parts.append("## Installer Information")
        prompt_parts.append(f"Application Name: {installer_metadata.name}")
        prompt_parts.append(f"Version: {installer_metadata.version}")
        prompt_parts.append(f"Vendor: {installer_metadata.vendor}")
        prompt_parts.append(f"Installer Type: {installer_metadata.installer_type.upper()}")
        prompt_parts.append(f"Architecture: {installer_metadata.architecture}")
        prompt_parts.append(f"Language: {installer_metadata.language}")

        if installer_metadata.installer_path:
            prompt_parts.append(f"Installer Path: {installer_metadata.installer_path}")

        if installer_metadata.silent_args:
            prompt_parts.append(f"Silent Install Arguments: {installer_metadata.silent_args}")

        if installer_metadata.uninstall_args:
            prompt_parts.append(f"Uninstall Arguments: {installer_metadata.uninstall_args}")

        if installer_metadata.notes:
            prompt_parts.append(f"Installer Notes: {installer_metadata.notes}")

        # Add user notes if provided
        if user_notes and user_notes.strip():
            prompt_parts.append("\n## Additional Requirements")
            prompt_parts.append(user_notes.strip())

        # Add RAG context if available
        if rag_context:
            prompt_parts.append("\n## PSADT Documentation Context")
            prompt_parts.append("The following documentation excerpts are relevant to your task:")

            for i, result in enumerate(rag_context[:8], 1):  # Limit to top 8 results
                prompt_parts.append(f"\n### Context {i} (Score: {result.score:.3f})")
                prompt_parts.append(f"Source: {result.document.metadata.get('filename', 'Unknown')}")
                # Truncate very long content
                content = result.document.content
                if len(content) > 2000:
                    content = content[:2000] + "...[truncated]"
                prompt_parts.append(content)

        # Add final instructions
        prompt_parts.append("\n## Task")
        prompt_parts.append(
            "Generate a complete PSADT v3.9+ PowerShell script for this installer. "
            "The script should be production-ready and follow all PSADT best practices. "
            "Include proper error handling, logging, user interaction, and support for "
            "Install/Uninstall/Repair operations."
        )

        return "\n".join(prompt_parts)

    def build_validation_prompt(self, script_content: str) -> List[Dict[str, str]]:
        """Build prompt for script validation.

        Args:
            script_content: Generated PSADT script content

        Returns:
            List of messages for validation
        """
        system_prompt = """You are a PSADT script validator. Review the provided PowerShell script
and identify any issues, improvements, or non-compliance with PSADT v3.9+ standards.

Check for:
1. Proper PSADT structure and required sections
2. Correct variable declarations
3. Appropriate error handling
4. Proper use of PSADT functions
5. Syntax correctness
6. Best practice compliance
7. Security considerations

Provide a JSON response with the following keys:
- "valid": boolean indicating if script is valid
- "issues": array of issue descriptions
- "suggestions": array of improvement suggestions
- "score": numeric score from 0-100"""

        user_prompt = (
            f"Please validate this PSADT script:\n\n"
            f"```powershell\n{script_content}\n```\n\n"
            "Respond with a JSON object containing your validation results."
        )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]


def build_rag_query(installer_metadata: InstallerMetadata, user_notes: Optional[str] = None) -> str:
    """Build search query for RAG knowledge base lookup.

    Args:
        installer_metadata: Installer metadata
        user_notes: User notes

    Returns:
        Search query string
    """
    query_parts = []

    # Add installer type specific terms
    if installer_metadata.installer_type.lower() == "msi":
        query_parts.extend(["MSI", "Execute-MSI", "Windows Installer"])
    elif installer_metadata.installer_type.lower() == "exe":
        query_parts.extend(["EXE", "Execute-Process", "executable"])

    # Add application type if extractable from name
    app_name_lower = installer_metadata.name.lower()
    if any(term in app_name_lower for term in ["office", "word", "excel", "powerpoint"]):
        query_parts.append("Microsoft Office")
    elif any(term in app_name_lower for term in ["chrome", "firefox", "browser"]):
        query_parts.append("web browser")
    elif any(term in app_name_lower for term in ["java", "jre", "jdk"]):
        query_parts.append("Java runtime")
    elif any(term in app_name_lower for term in ["adobe", "acrobat", "reader"]):
        query_parts.append("Adobe")

    # Add user-specific terms from notes
    if user_notes:
        # Extract key terms from user notes
        notes_lower = user_notes.lower()
        if "silent" in notes_lower:
            query_parts.append("silent installation")
        if "registry" in notes_lower:
            query_parts.append("registry modification")
        if "service" in notes_lower:
            query_parts.append("Windows service")
        if "shortcut" in notes_lower:
            query_parts.append("desktop shortcut")

    # Add general PSADT terms
    query_parts.extend(["PSADT", "deployment", "installation"])

    # Join and return
    return " ".join(query_parts)
