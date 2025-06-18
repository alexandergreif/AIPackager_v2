"""Pydantic models for representing a structured PSADT script."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Command(BaseModel):
    """Represents a single command in a PSADT script section."""

    name: str = Field(..., description="The name of the PSADT function or cmdlet, e.g., 'Execute-Process'.")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Parameters for the command, e.g., {'Path': 'setup.exe'}."
    )
    comment: Optional[str] = Field(None, description="An optional comment for this command.")


class Section(BaseModel):
    """Represents a named section in a PSADT script, containing a list of commands."""

    name: str = Field(..., description="The name of the section, e.g., 'Installation', 'Pre-Uninstallation'.")
    commands: List[Command] = Field(
        default_factory=list, description="A list of commands to be executed in this section."
    )
    comment: Optional[str] = Field(None, description="An optional comment for this section.")


class PSADTScript(BaseModel):
    """Represents the overall structure of a PSADT script."""

    variables: Dict[str, str] = Field(
        default_factory=dict,
        description="Key-value pairs for script variables, e.g., {'appVendor': 'My Corp'}.",
    )
    custom_functions: List[str] = Field(
        default_factory=list, description="List of raw PowerShell custom function strings to be included."
    )

    pre_installation: Optional[Section] = Field(None, description="Commands for the Pre-Installation phase.")
    installation: Section = Field(..., description="Commands for the main Installation phase.")
    post_installation: Optional[Section] = Field(None, description="Commands for the Post-Installation phase.")

    pre_uninstallation: Optional[Section] = Field(None, description="Commands for the Pre-Uninstallation phase.")
    uninstallation: Optional[Section] = Field(None, description="Commands for the main Uninstallation phase.")
    post_uninstallation: Optional[Section] = Field(None, description="Commands for the Post-Uninstallation phase.")

    # Optional generic sections for flexibility, if needed by the LLM
    # For example, if the LLM wants to define a "User Experience" section not tied to a phase.
    # However, sticking to PSADT phases is generally better.
    # custom_sections: List[Section] = Field(default_factory=list, description="Additional custom sections.")

    class Config:
        """Pydantic model configuration."""

        extra = "forbid"  # Disallow extra fields not defined in the model
        anystr_strip_whitespace = True
        validate_assignment = True
