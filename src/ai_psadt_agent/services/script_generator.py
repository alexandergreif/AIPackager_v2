"""Main script generation service that orchestrates the complete pipeline."""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from loguru import logger

from .knowledge_base import initialize_knowledge_base
from .llm_client import LLMMessage, get_llm_provider
from .prompt_templates import InstallerMetadata, PromptBuilder, build_rag_query


@dataclass
class GenerationResult:
    """Result from script generation."""

    script_content: str
    metadata: Dict[str, Any]
    validation_score: float
    issues: List[str]
    suggestions: List[str]
    rag_sources: List[str]


class ComplianceLinter:
    """PSADT compliance linter for script validation."""

    def __init__(self) -> None:
        """Initialize the compliance linter."""
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
        """Validate PSADT script for compliance.

        Args:
            script_content: PowerShell script content

        Returns:
            Validation results
        """
        issues = []
        suggestions = []
        score = 100

        # Check required patterns
        for pattern in self.required_patterns:
            if not re.search(pattern, script_content, re.IGNORECASE):
                issues.append(f"Missing required pattern: {pattern}")
                score -= 10

        # Check recommended patterns
        missing_recommended = 0
        for pattern in self.recommended_patterns:
            if not re.search(pattern, script_content, re.IGNORECASE):
                suggestions.append(f"Consider adding: {pattern}")
                missing_recommended += 1

        # Deduct points for missing recommended patterns
        score -= missing_recommended * 2

        # Check for security issues
        for pattern in self.security_patterns:
            if re.search(pattern, script_content, re.IGNORECASE):
                issues.append(f"Security concern: {pattern}")
                score -= 15

        # Check script length (should be substantial)
        lines = script_content.split("\n")
        if len(lines) < 50:
            issues.append("Script appears too short for a complete PSADT deployment")
            score -= 20

        # Check for proper structure
        if not re.search(r"##\*.*VARIABLE DECLARATION.*\*##", script_content, re.IGNORECASE):
            issues.append("Missing proper VARIABLE DECLARATION section")
            score -= 10

        if not re.search(r"##\*.*INSTALLATION.*\*##", script_content, re.IGNORECASE):
            issues.append("Missing proper INSTALLATION section")
            score -= 10

        # Ensure score doesn't go below 0
        score = max(0, score)

        return {
            "valid": score >= 70,
            "score": score,
            "issues": issues,
            "suggestions": suggestions,
        }


class ScriptGenerator:
    """Main script generation orchestrator."""

    def __init__(self) -> None:
        """Initialize the script generator."""
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
    ) -> Optional[GenerationResult]:  # Changed to Optional[GenerationResult]
        """Generate PSADT script with validation and retry logic.

        Args:
            installer_metadata: Metadata about the installer
            user_notes: Additional user requirements
            max_retries: Maximum number of retry attempts

        Returns:
            Generation result with script and validation info
        """
        logger.info(f"Generating PSADT script for {installer_metadata.name} v{installer_metadata.version}")

        # Build RAG query and search knowledge base
        rag_query = build_rag_query(installer_metadata, user_notes)
        logger.debug(f"RAG query: {rag_query}")

        rag_results = self.knowledge_base.search(rag_query, top_k=8)
        rag_sources = [result.document.metadata.get("filename", "Unknown") for result in rag_results]

        logger.info(f"Found {len(rag_results)} relevant documentation chunks")

        # Build generation prompt
        messages = self.prompt_builder.build_generation_prompt(
            installer_metadata=installer_metadata,
            user_notes=user_notes,
            rag_context=rag_results,
        )

        # Convert to LLM format
        llm_messages = [LLMMessage(role=msg["role"], content=msg["content"]) for msg in messages]

        best_result = None
        best_score = 0

        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Generation attempt {attempt + 1}/{max_retries + 1}")

                # Generate script
                response = self.llm_provider.generate(messages=llm_messages, max_tokens=4000, temperature=0.1)

                script_content = self._extract_script_content(response.content)

                # Validate script
                validation_result = self.compliance_linter.validate_script(script_content)

                logger.info(f"Generated script with validation score: {validation_result['score']}")

                # If this is the best result so far, save it
                if validation_result["score"] > best_score:
                    best_score = validation_result["score"]
                    best_result = GenerationResult(
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

                # If validation passed, return result
                if validation_result["valid"]:
                    logger.info(f"Script generation successful on attempt {attempt + 1}")
                    return best_result

                # If not valid and we have retries left, try again
                if attempt < max_retries:
                    logger.warning(f"Script validation failed (score: {validation_result['score']}), retrying...")
                    # Add validation feedback to next attempt
                    feedback_message = self._build_feedback_message(validation_result)
                    llm_messages.append(LLMMessage(role="user", content=feedback_message))

            except Exception as e:
                logger.error(f"Error during generation attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries:
                    raise
                continue

        # Return best result even if not fully valid
        if best_result:
            logger.warning(f"Returning best result with score {best_score} after {max_retries + 1} attempts")
            assert best_result is not None
            return best_result
        else:
            # If loop completes and best_result is still None (e.g. all attempts failed before setting best_result)
            # This path will now return None as per Optional[GenerationResult]
            # However, the original logic was to raise RuntimeError.
            # To maintain original behavior while satisfying type checker for now:
            # If we reach here and best_result is None, it means no script was ever generated.
            # The RuntimeError is more appropriate than returning None if a result is always expected.
            # For now, to pass Mypy with Optional, this path would return None.
            # Let's keep the raise for now and see if Mypy is happy with Optional and a path that raises.
            # If not, I'll have to return None here.
            # The error was "Incompatible return value type (got "GenerationResult | None", expected "GenerationResult")"
            # This means Mypy thought a None *could* be returned.
            # If best_result is None here, it means no GenerationResult was ever created.
            # The only way to get None is if the loop doesn't run and best_result is not updated.
            # If max_retries = -1, range(0) is empty. best_result is None.
            # Then `if best_result:` is false. It will hit the `else` and raise.
            # So, the function should always return GenerationResult or raise.
            # The Mypy error is likely due to its flow analysis of `best_result = None` initialization.
            # The `assert best_result is not None` should have fixed it.
            # Let's try changing the return type to Optional and see if that makes Mypy happy,
            # and then adjust the calling code if needed.
            # For now, I will keep the raise and the Optional return type.
            # Mypy might complain that not all paths return Optional[GenerationResult] if one raises.
            # Let's revert the assert and the logger.error for now, and just change the return type.
            # The original problem was that `return best_result` (where best_result could be None)
            # was incompatible with `-> GenerationResult`.
            # If the function returns `Optional[GenerationResult]`, then `return best_result` is fine.
            # The `raise RuntimeError` means not all code paths return.
            # This is fine for Mypy if the return type is `NoReturn` for that path, or if the overall
            # function return type accounts for paths that don't return.
            # Let's stick to the `Optional[GenerationResult]` and see.
            # The error was on line 209, which is `return best_result` inside the loop.
            # At that point, best_result is definitely a GenerationResult.
            # The issue might be the final `return best_result` if the loop never runs.
            # If max_retries = -1, loop doesn't run, best_result is None.
            # `if best_result:` (None) is false. `else: raise`. This path is fine.
            # The problem is likely Mypy's inference.
            # The assert I added was for the *final* return, not the one inside the loop.
            # Let's add an assert for the one inside the loop too.
            # Actually, if `validation_result["valid"]` is true, `best_result` *must* have been set.
            # This error is very subtle.
            # Let's try the `cast` for `_extract_script_content` first.
            logger.error("No script could be generated after all attempts or retries.")  # noqa: E501
            raise RuntimeError("Failed to generate any valid script after all attempts")

    def _extract_script_content(self, llm_response: str) -> str:
        """Extract PowerShell script content from LLM response.

        Args:
            llm_response: Raw LLM response

        Returns:
            Extracted script content
        """
        # Look for PowerShell code blocks
        powershell_pattern = r"```(?:powershell|ps1)?\s*\n(.*?)```"
        matches = re.findall(powershell_pattern, llm_response, re.DOTALL | re.IGNORECASE)

        if matches:
            # Return the longest match (most likely the main script)
            longest_match: str = max(matches, key=len)
            return longest_match.strip()

        # If no code blocks found, look for script-like content
        # Check if response starts with PowerShell comment block
        if llm_response.strip().startswith("<#") or llm_response.strip().startswith("#"):
            return llm_response.strip()

        # Try to extract content that looks like a PowerShell script
        lines = llm_response.split("\n")
        script_lines: list[str] = []
        in_script = False

        for line in lines:
            if any(keyword in line.lower() for keyword in ["param(", "try {", "$app", "show-installation"]):
                in_script = True

            if in_script:
                script_lines.append(line)

        if script_lines:
            return "\n".join(script_lines).strip()

        # Fallback: return the entire response
        logger.warning("Could not extract script content, returning full response")
        return llm_response.strip()

    def _build_feedback_message(self, validation_result: Dict[str, Any]) -> str:
        """Build feedback message for script improvement.

        Args:
            validation_result: Validation result from compliance linter

        Returns:
            Feedback message
        """
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
    """Factory function to get script generator instance.

    Returns:
        ScriptGenerator instance
    """
    return ScriptGenerator()
