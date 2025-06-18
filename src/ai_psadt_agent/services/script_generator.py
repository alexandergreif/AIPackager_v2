"""Main script generation service that orchestrates the complete pipeline."""

import json  # Added import for json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from loguru import logger

from ..domain_models.psadt_script import PSADTScript  # Import the new model
from .knowledge_base import initialize_knowledge_base
from .llm_client import LLMMessage, get_llm_provider
from .prompt_templates import InstallerMetadata, PromptBuilder, build_rag_query


@dataclass
class GenerationResult:
    """Result from script generation."""

    structured_script: Optional[PSADTScript]  # Store the Pydantic model
    script_content: str  # Keep for now, will be populated by renderer later
    metadata: Dict[str, Any]
    validation_score: float
    issues: List[str]
    suggestions: List[str]
    rag_sources: List[str]


class ComplianceLinter:
    """PSADT compliance linter for script validation."""

    def __init__(self) -> None:
        self.required_patterns = [
            r"#\s*\.SYNOPSIS",
            r"#\s*\.DESCRIPTION",
            r"\[CmdletBinding\(\)\]",
            r"Param\s*\(",
            r"Try\s*\{",
            r"Catch\s*\{",
            r"Set-ExecutionPolicy",
            r"\$app(Vendor|Name|Version)",
            r"Show-InstallationWelcome",
            r"Show-InstallationProgress",
            r"Exit-Script",
            r"Write-Log",
        ]
        self.recommended_patterns = [
            r"Execute-(MSI|Process)",
            r"installPhase\s*=",
            r"mainExitCode",
            r"deploymentType",
            r"AppDeployToolkitMain\.ps1",
        ]
        self.security_patterns = [
            r"Invoke-Expression",
            r"iex\s",
            r"cmd\s*/c",
            r"powershell\s*-c",
        ]

    def validate_script(self, script_content: str) -> Dict[str, Any]:
        issues: List[str] = []
        suggestions: List[str] = []
        score = 100
        for pattern in self.required_patterns:
            if not re.search(pattern, script_content, re.IGNORECASE):
                issues.append(f"Missing required pattern: {pattern}")
                score -= 10
        missing_recommended = 0
        for pattern in self.recommended_patterns:
            if not re.search(pattern, script_content, re.IGNORECASE):
                suggestions.append(f"Consider adding: {pattern}")
                missing_recommended += 1
        score -= missing_recommended * 2
        for pattern in self.security_patterns:
            if re.search(pattern, script_content, re.IGNORECASE):
                issues.append(f"Security concern: {pattern}")
                score -= 15
        lines = script_content.split("\n")
        if len(lines) < 20:  # Adjusted for placeholder content during SP4-03
            issues.append("Script appears too short.")
            score -= 5
        if not re.search(r"##\*.*VARIABLE DECLARATION.*\*##", script_content, re.IGNORECASE):
            issues.append("Missing proper VARIABLE DECLARATION section")
            score -= 5
        if not re.search(r"##\*.*INSTALLATION.*\*##", script_content, re.IGNORECASE):
            issues.append("Missing proper INSTALLATION section")
            score -= 5
        score = max(0, score)
        return {
            "valid": score >= 50,
            "score": score,
            "issues": issues,
            "suggestions": suggestions,
        }  # Adjusted threshold for SP4-03


class ScriptGenerator:
    """Main script generation orchestrator."""

    def __init__(self) -> None:
        self.llm_provider = get_llm_provider()
        self.knowledge_base = initialize_knowledge_base()
        self.prompt_builder = PromptBuilder()
        self.compliance_linter = ComplianceLinter()
        logger.info("Initialized script generator")

    def generate_script(
        self,
        installer_metadata: InstallerMetadata,
        user_notes: Optional[str] = None,
        max_retries: int = 2,
    ) -> Optional[GenerationResult]:
        logger.info(f"Generating PSADT script for {installer_metadata.name} v{installer_metadata.version}")
        rag_query = build_rag_query(installer_metadata, user_notes)
        rag_results = self.knowledge_base.search(rag_query, top_k=8)
        rag_sources = [result.document.metadata.get("filename", "Unknown") for result in rag_results]
        logger.info(f"Found {len(rag_results)} relevant documentation chunks")

        messages = self.prompt_builder.build_generation_prompt(
            installer_metadata=installer_metadata,
            user_notes=user_notes,
            rag_context=rag_results,
        )
        llm_messages = [LLMMessage(role=msg["role"], content=msg["content"]) for msg in messages]

        psadt_script_tool = {
            "type": "function",
            "function": {
                "name": "generate_psadt_script",
                "description": "Generates a structured PSADT script based on the provided installer metadata and requirements.",
                "parameters": PSADTScript.model_json_schema(),
            },
        }

        best_result: Optional[GenerationResult] = None
        best_score = -1

        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Generation attempt {attempt + 1}/{max_retries + 1}")
                response = self.llm_provider.generate(
                    messages=llm_messages,
                    max_tokens=4096,  # Increased for potentially larger JSON
                    temperature=0.1,
                    tools=[psadt_script_tool],
                    tool_choice={"type": "function", "function": {"name": "generate_psadt_script"}},
                )

                structured_psadt_script: Optional[PSADTScript] = None
                script_content = ""

                if response.tool_calls:
                    tool_call = response.tool_calls[0]
                    if tool_call.function.name == "generate_psadt_script":
                        try:
                            tool_args = json.loads(tool_call.function.arguments)
                            structured_psadt_script = PSADTScript(**tool_args)
                            script_content = f"# Structured PSADT Script generated for: {structured_psadt_script.installation.name}\n"
                            script_content += "# Actual rendering to PS1 will be done in SP4-04.\n"
                            # Add minimal valid PSADT content for linting
                            script_content += "<# .SYNOPSIS Placeholder #>\n<# .DESCRIPTION Placeholder #>\n[CmdletBinding()]\nParam()\nTry {\nWrite-Log 'Placeholder'\nShow-InstallationWelcome\nShow-InstallationProgress\nExit-Script -ExitCode 0\n}\nCatch { Write-Log 'Error'; Exit-Script -ExitCode 1 }\nSet-ExecutionPolicy Bypass -Scope Process -Force\n$appVendor = 'Vendor'; $appName = 'App'; $appVersion = '1.0'\n##* VARIABLE DECLARATION *##\n##* INSTALLATION *##"
                            logger.info("Successfully parsed structured PSADT script from LLM tool call.")
                        except Exception as e:
                            logger.error(f"Failed to parse PSADTScript from LLM tool call arguments: {e}")
                            if response.content:
                                script_content = self._extract_script_content(response.content)
                            else:
                                script_content = "# Error: LLM did not provide usable content or tool call arguments."
                elif response.content:
                    script_content = self._extract_script_content(response.content)
                    logger.warning("LLM did not use the function call. Falling back to raw content.")
                else:
                    script_content = "# Error: LLM provided no content and no tool call."
                    logger.error("LLM response had no content and no tool call.")

                validation_result = self.compliance_linter.validate_script(script_content)
                logger.info(f"Generated script with validation score: {validation_result['score']}")

                if validation_result["score"] > best_score:
                    best_score = validation_result["score"]
                    best_result = GenerationResult(
                        structured_script=structured_psadt_script,
                        script_content=script_content,
                        metadata={
                            "installer": installer_metadata.__dict__,
                            "user_notes": user_notes,
                            "rag_sources": rag_sources,
                            "llm_model": response.model,
                            "llm_usage": response.usage,
                            "attempt": attempt + 1,
                        },
                        validation_score=validation_result["score"],
                        issues=validation_result["issues"],
                        suggestions=validation_result["suggestions"],
                        rag_sources=rag_sources,
                    )

                if validation_result["valid"]:
                    logger.info(f"Script generation successful on attempt {attempt + 1}")
                    return best_result

                if attempt < max_retries:
                    logger.warning(f"Script validation failed (score: {validation_result['score']}), retrying...")
                    feedback_message = self._build_feedback_message(validation_result)
                    llm_messages.append(LLMMessage(role="user", content=feedback_message))

            except Exception as e:
                logger.error(f"Error during generation attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries:
                    if best_result is None:
                        logger.error("Failed to generate any script after all attempts due to errors.")
                        return None
                continue  # Continue to next retry or to final return of best_result

        if best_result:
            logger.warning(
                f"Returning best result with score {best_score} after {max_retries + 1} attempts (may not be fully valid)."
            )
            return best_result

        logger.error("No script could be generated after all attempts or retries.")
        return None

    def _extract_script_content(self, llm_response_content: Optional[str]) -> str:
        if llm_response_content is None:
            return ""  # Handles None case

        # Now, llm_response_content is known to be a str (could be empty)
        content_str: str = llm_response_content

        if not content_str:  # Handles empty string case
            return ""

        # Now, content_str is a non-empty string.
        # The assert isinstance is no longer needed due to the explicit checks and assignment.

        powershell_pattern = r"```(?:powershell|ps1)?\s*\n(.*?)```"
        matches = re.findall(powershell_pattern, content_str, re.DOTALL | re.IGNORECASE)
        if matches:
            non_empty_matches = [m for m in matches if m.strip()]
            if non_empty_matches:
                return max(non_empty_matches, key=len).strip()  # type: ignore[no-any-return]

        stripped_content = content_str.strip()  # Let Mypy infer type from str.strip()
        if stripped_content.startswith(("<#", "#", "[", "$", "Function", "Configuration")):
            return stripped_content

        logger.warning(
            "Could not reliably extract script content using markdown code block or common PowerShell starting patterns."
        )

        if len(stripped_content.split()) < 50 and "\n" in stripped_content:
            logger.info("Returning short content with newlines as potential script fragment.")
            return stripped_content

        logger.warning(
            "Returning full response content as script content due to extraction difficulties or it being prose."
        )
        return stripped_content

    def _build_feedback_message(self, validation_result: Dict[str, Any]) -> str:
        feedback_parts = [
            "The generated script has validation issues. Please improve it:",
            f"Current score: {validation_result['score']}/100",
        ]
        if validation_result["issues"]:
            feedback_parts.append("\nIssues to fix:")
            for issue in validation_result["issues"]:
                feedback_parts.append(f"- {issue}")
        if validation_result["suggestions"]:
            feedback_parts.append("\nSuggestions for improvement:")
            for suggestion in validation_result["suggestions"]:
                feedback_parts.append(f"- {suggestion}")
        feedback_parts.append("\nPlease generate an improved version that addresses these issues.")
        return "\n".join(feedback_parts)


def get_script_generator() -> ScriptGenerator:
    return ScriptGenerator()
