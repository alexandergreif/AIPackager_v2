"""
This script generates a sample PSADT script for testing purposes.
It uses the application's services to generate the script.
"""

from ai_psadt_agent.services.prompt_templates import InstallerMetadata
from ai_psadt_agent.services.script_generator import ScriptGenerator


def main():
    """Main function to generate the test script."""
    generator = ScriptGenerator()
    metadata = InstallerMetadata(
        name="Test App for Smoke Test",
        version="1.0.0",
        vendor="Test Vendor",
        installer_type="msi",
    )
    result = generator.generate_script(metadata)

    with open("generated_script.ps1", "w", encoding="utf-8") as f:
        f.write(result.script_content)


if __name__ == "__main__":
    main()
