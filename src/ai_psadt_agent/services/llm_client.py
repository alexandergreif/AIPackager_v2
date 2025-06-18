"""LLM client with provider interface and OpenAI implementation."""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import openai
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()


@dataclass
class LLMMessage:
    """Represents a message in the conversation."""

    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """Response from LLM provider."""

    content: str
    usage: Optional[Dict[str, Any]] = None
    model: Optional[str] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(
        self,
        messages: List[LLMMessage],
        max_tokens: Optional[int] = None,
        temperature: float = 0.1,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate response from messages."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of the provider."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key. If None, will read from OPENAI_API_KEY env var.
            model: Model to use for generation.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        self.model = model
        self.client = openai.OpenAI(api_key=self.api_key)
        logger.info(f"Initialized OpenAI provider with model: {self.model}")

    def generate(
        self,
        messages: List[LLMMessage],
        max_tokens: Optional[int] = None,
        temperature: float = 0.1,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate response using OpenAI API."""
        try:
            # Convert messages to OpenAI format
            openai_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

            logger.debug(f"Sending {len(openai_messages)} messages to OpenAI")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )

            content = response.choices[0].message.content or ""
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            }

            logger.info(f"Generated response with {usage['total_tokens']} tokens")

            return LLMResponse(
                content=content,
                usage=usage,
                model=self.model,
            )

        except Exception as e:
            logger.error(f"Error generating response from OpenAI: {str(e)}")
            raise

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "openai"


class AnthropicProvider(LLMProvider):
    """Placeholder for Anthropic provider - to be implemented in future."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-sonnet-20240229"):
        """Initialize Anthropic provider."""
        raise NotImplementedError("Anthropic provider not yet implemented")

    def generate(
        self,
        messages: List[LLMMessage],
        max_tokens: Optional[int] = None,
        temperature: float = 0.1,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate response using Anthropic API."""
        raise NotImplementedError("Anthropic provider not yet implemented")

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "anthropic"


class GeminiProvider(LLMProvider):
    """Placeholder for Google Gemini provider - to be implemented in future."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-pro"):
        """Initialize Gemini provider."""
        raise NotImplementedError("Gemini provider not yet implemented")

    def generate(
        self,
        messages: List[LLMMessage],
        max_tokens: Optional[int] = None,
        temperature: float = 0.1,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate response using Gemini API."""
        raise NotImplementedError("Gemini provider not yet implemented")

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "gemini"


def get_llm_provider(provider_name: Optional[str] = None) -> LLMProvider:
    """Factory function to get LLM provider.

    Args:
        provider_name: Name of provider ("openai", "anthropic", "gemini").
                      If None, reads from LLM_PROVIDER env var, defaults to "openai".

    Returns:
        LLM provider instance.

    Raises:
        ValueError: If provider is not supported.
    """
    if provider_name is None:
        provider_name = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider_name == "openai":
        return OpenAIProvider()
    elif provider_name == "anthropic":
        return AnthropicProvider()
    elif provider_name == "gemini":
        return GeminiProvider()
    else:
        raise ValueError(f"Unsupported LLM provider: {provider_name}")
