"""Script renderer service using Jinja2 templates."""

from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader
from loguru import logger

from ..domain_models.psadt_script import PSADTScript


class ScriptRenderer:
    """Renders PSADTScript models to PowerShell scripts using Jinja2 templates."""

    def __init__(self, templates_dir: str = "templates"):
        """Initialize the renderer with template directory.

        Args:
            templates_dir: Directory containing Jinja2 templates, relative to the package root
        """
        # Get the package root directory (src/ai_psadt_agent)
        package_root = Path(__file__).parent.parent
        templates_path = package_root / templates_dir

        if not templates_path.exists():
            raise FileNotFoundError(f"Templates directory not found: {templates_path}")

        self.env = Environment(
            loader=FileSystemLoader(str(templates_path)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        logger.info(f"Initialized script renderer with templates from: {templates_path}")

    def render_psadt_script(self, psadt_script: PSADTScript, template_name: str = "Deploy-Application.ps1.j2") -> str:
        """Render a PSADTScript to a PowerShell script string.

        Args:
            psadt_script: The PSADTScript model to render
            template_name: Name of the Jinja2 template file

        Returns:
            Rendered PowerShell script as a string
        """
        try:
            template = self.env.get_template(template_name)

            # Convert the PSADTScript to a dict for template rendering
            template_context = self._prepare_template_context(psadt_script)

            rendered_script = template.render(**template_context)

            logger.info(f"Successfully rendered PSADT script using template: {template_name}")
            return rendered_script

        except Exception as e:
            logger.error(f"Error rendering PSADT script with template {template_name}: {str(e)}")
            raise

    def _prepare_template_context(self, psadt_script: PSADTScript) -> Dict[str, Any]:
        """Prepare the template context from a PSADTScript model.

        Args:
            psadt_script: The PSADTScript model

        Returns:
            Dictionary with template variables
        """
        context = {
            "variables": psadt_script.variables,
            "custom_functions": psadt_script.custom_functions,
            "pre_installation": psadt_script.pre_installation,
            "installation": psadt_script.installation,
            "post_installation": psadt_script.post_installation,
            "pre_uninstallation": psadt_script.pre_uninstallation,
            "uninstallation": psadt_script.uninstallation,
            "post_uninstallation": psadt_script.post_uninstallation,
        }

        return context


def get_script_renderer() -> ScriptRenderer:
    """Factory function to get script renderer instance."""
    return ScriptRenderer()
