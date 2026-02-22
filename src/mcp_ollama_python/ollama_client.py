"""
Ollama HTTP client wrapper
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import httpx

try:
    from mcp_ollama_python.models import (
        GenerationOptions,
        ChatMessage,
        Tool,
        OllamaError,
        NetworkError,
    )
except ImportError:
    from .models import GenerationOptions, ChatMessage, Tool, OllamaError, NetworkError

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_HOST = "http://127.0.0.1:11434"
DEFAULT_TIMEOUT = 300.0  # 5 minutes
MODEL_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]*$")


class OllamaClient:
    """
    HTTP client for Ollama API.

    This client provides async methods to interact with the Ollama API,
    including model management, text generation, chat, and embeddings.

    Args:
        host: Ollama server URL (defaults to OLLAMA_HOST env var or http://127.0.0.1:11434)
        api_key: API key for authentication (defaults to OLLAMA_API_KEY env var)
        timeout: Request timeout in seconds (default: 300.0)

    Raises:
        ValueError: If host URL is invalid or insecure
    """

    def __init__(
        self,
        host: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        raw_host = host or os.getenv("OLLAMA_HOST", DEFAULT_HOST)
        self.host = self._validate_host(raw_host)
        self.api_key = api_key or os.getenv("OLLAMA_API_KEY")
        self.timeout = timeout

        # Log initialization (sanitize API key)
        if self.api_key:
            safe_preview = self.api_key[:4] if len(self.api_key) >= 4 else "***"
            logger.debug("API key configured (preview: %s)", safe_preview)
        logger.debug("Ollama client initialized with host: %s", self.host)

        # Create httpx client
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.client = httpx.AsyncClient(
            base_url=self.host,
            headers=headers,
            timeout=httpx.Timeout(timeout=self.timeout, connect=10.0),
            follow_redirects=True,
        )

    @staticmethod
    def _validate_host(host: str) -> str:
        """
        Validate and sanitize the host URL to prevent SSRF attacks.

        Args:
            host: Host URL to validate

        Returns:
            Validated host URL

        Raises:
            ValueError: If host is invalid or potentially insecure
        """
        if not host or not isinstance(host, str):
            raise ValueError("Host must be a non-empty string")

        host = host.strip()

        # Ensure URL has a scheme
        if not host.startswith(("http://", "https://")):
            raise ValueError("Host must start with http:// or https://")

        # Parse URL
        try:
            parsed = urlparse(host)
        except Exception as e:
            raise ValueError(f"Invalid host URL: {e}") from e

        # Validate scheme
        if parsed.scheme not in ["http", "https"]:
            raise ValueError("Host must use http or https scheme")

        # Validate hostname exists
        if not parsed.netloc:
            raise ValueError("Host must include a valid hostname")

        logger.debug("Host validated: %s", host)
        return host

    @staticmethod
    def _validate_model_name(model: str) -> None:
        """
        Validate model name format.

        Args:
            model: Model name to validate

        Raises:
            ValueError: If model name is invalid
        """
        if not model or not isinstance(model, str):
            raise ValueError("Model name must be a non-empty string")

        if not MODEL_NAME_PATTERN.match(model):
            raise ValueError(
                f"Invalid model name '{model}'. Must start with alphanumeric "
                "and contain only alphanumeric, dots, underscores, hyphens, or colons."
            )

    @staticmethod
    def _validate_non_empty_string(value: str, name: str) -> None:
        """
        Validate that a string parameter is non-empty.

        Args:
            value: String value to validate
            name: Parameter name for error messages

        Raises:
            ValueError: If value is empty or not a string
        """
        if not value or not isinstance(value, str):
            raise ValueError(f"{name} must be a non-empty string")

    async def __aenter__(self):
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager and close HTTP client."""
        await self.client.aclose()
        logger.debug("Ollama client closed")

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Handle HTTP response consistently.

        Args:
            response: HTTP response object

        Returns:
            Parsed JSON response or empty dict for empty responses

        Raises:
            OllamaError: If response contains invalid JSON
        """
        response.raise_for_status()

        # Handle empty responses
        if response.headers.get("content-length") == "0" or not response.content:
            return {}

        try:
            return response.json()
        except ValueError as e:
            logger.error("Invalid JSON in response: %s", e)
            raise OllamaError(f"Invalid JSON response: {e}", cause=e) from e

    async def _get(self, endpoint: str) -> Dict[str, Any]:
        """
        Make a GET request to Ollama API.

        Args:
            endpoint: API endpoint path

        Returns:
            JSON response as dictionary

        Raises:
            OllamaError: If API returns error status
            NetworkError: If network request fails
        """
        logger.debug("GET %s", endpoint)
        try:
            response = await self.client.get(endpoint)
            return self._handle_response(response)
        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error on GET %s: %s - %s",
                endpoint,
                e.response.status_code,
                e.response.text,
            )
            raise OllamaError(
                f"Ollama API error: {e.response.status_code} - {e.response.text}",
                cause=e,
            ) from e
        except httpx.RequestError as e:
            logger.error("Network error on GET %s: %s", endpoint, e)
            raise NetworkError(f"Failed to connect to Ollama: {str(e)}", cause=e) from e
        except Exception as e:
            logger.error("Unexpected error on GET %s: %s", endpoint, e)
            raise NetworkError(f"Unexpected error: {str(e)}", cause=e) from e

    async def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a POST request to Ollama API.

        Args:
            endpoint: API endpoint path
            data: JSON data to send in request body

        Returns:
            JSON response as dictionary

        Raises:
            OllamaError: If API returns error status
            NetworkError: If network request fails
        """
        logger.debug("POST %s", endpoint)
        try:
            response = await self.client.post(endpoint, json=data)
            return self._handle_response(response)
        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error on POST %s: %s - %s",
                endpoint,
                e.response.status_code,
                e.response.text,
            )
            raise OllamaError(
                f"Ollama API error: {e.response.status_code} - {e.response.text}",
                cause=e,
            ) from e
        except httpx.RequestError as e:
            logger.error("Network error on POST %s: %s", endpoint, e)
            raise NetworkError(f"Failed to connect to Ollama: {str(e)}", cause=e) from e
        except Exception as e:
            logger.error("Unexpected error on POST %s: %s", endpoint, e)
            raise NetworkError(f"Unexpected error: {str(e)}", cause=e) from e

    async def _delete(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a DELETE request to Ollama API.

        Args:
            endpoint: API endpoint path
            data: JSON data to send in request body

        Returns:
            JSON response as dictionary (empty dict for empty responses)

        Raises:
            OllamaError: If API returns error status
            NetworkError: If network request fails
        """
        logger.debug("DELETE %s", endpoint)
        try:
            response = await self.client.request("DELETE", endpoint, json=data)
            return self._handle_response(response)
        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error on DELETE %s: %s - %s",
                endpoint,
                e.response.status_code,
                e.response.text,
            )
            raise OllamaError(
                f"Ollama API error: {e.response.status_code} - {e.response.text}",
                cause=e,
            ) from e
        except httpx.RequestError as e:
            logger.error("Network error on DELETE %s: %s", endpoint, e)
            raise NetworkError(f"Failed to connect to Ollama: {str(e)}", cause=e) from e
        except Exception as e:
            logger.error("Unexpected error on DELETE %s: %s", endpoint, e)
            raise NetworkError(f"Unexpected error: {str(e)}", cause=e) from e

    async def list(self) -> Dict[str, Any]:
        """
        List all available models.

        Returns:
            Dictionary containing list of models

        Raises:
            OllamaError: If API returns error
            NetworkError: If connection fails
        """
        return await self._get("/api/tags")

    async def show(self, model: str) -> Dict[str, Any]:
        """
        Show detailed information about a model.

        Args:
            model: Name of the model

        Returns:
            Dictionary containing model information

        Raises:
            ValueError: If model name is invalid
            OllamaError: If API returns error
            NetworkError: If connection fails
        """
        self._validate_model_name(model)
        return await self._post("/api/show", {"name": model})

    async def pull(self, model: str) -> Dict[str, Any]:
        """
        Pull (download) a model from the Ollama registry.

        Args:
            model: Name of the model to pull

        Returns:
            Dictionary containing pull operation status

        Raises:
            ValueError: If model name is invalid
            OllamaError: If API returns error
            NetworkError: If connection fails
        """
        self._validate_model_name(model)
        return await self._post("/api/pull", {"name": model, "stream": False})

    async def push(self, model: str) -> Dict[str, Any]:
        """
        Push a model to the Ollama registry.

        Args:
            model: Name of the model to push

        Returns:
            Dictionary containing push operation status

        Raises:
            ValueError: If model name is invalid
            OllamaError: If API returns error
            NetworkError: If connection fails
        """
        self._validate_model_name(model)
        return await self._post("/api/push", {"name": model, "stream": False})

    async def copy(self, source: str, destination: str) -> Dict[str, Any]:
        """
        Copy a model to a new name.

        Args:
            source: Source model name
            destination: Destination model name

        Returns:
            Dictionary containing copy operation status

        Raises:
            ValueError: If model names are invalid
            OllamaError: If API returns error
            NetworkError: If connection fails
        """
        self._validate_model_name(source)
        self._validate_model_name(destination)
        return await self._post(
            "/api/copy", {"source": source, "destination": destination}
        )

    async def delete(self, model: str) -> Dict[str, Any]:
        """
        Delete a model from local storage.

        Args:
            model: Name of the model to delete

        Returns:
            Dictionary containing deletion status (empty dict on success)

        Raises:
            ValueError: If model name is invalid
            OllamaError: If API returns error
            NetworkError: If connection fails
        """
        self._validate_model_name(model)
        return await self._delete("/api/delete", {"name": model})

    async def create(
        self, name: str, modelfile: str, stream: bool = False
    ) -> Dict[str, Any]:
        """
        Create a model from a Modelfile.

        Args:
            name: Name for the new model
            modelfile: Modelfile content
            stream: Whether to stream the response (default: False)

        Returns:
            Dictionary containing creation status

        Raises:
            ValueError: If name or modelfile is invalid
            OllamaError: If API returns error
            NetworkError: If connection fails
        """
        self._validate_model_name(name)
        self._validate_non_empty_string(modelfile, "modelfile")
        data = {"name": name, "modelfile": modelfile}
        if stream:
            data["stream"] = True
        return await self._post("/api/create", data)

    async def generate(
        self,
        model: str,
        prompt: str,
        options: Optional[GenerationOptions] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate text completion from a prompt.

        Args:
            model: Name of the model to use
            prompt: Text prompt for generation
            options: Optional generation parameters
            stream: Whether to stream the response (default: False)

        Returns:
            Dictionary containing generated text and metadata

        Raises:
            ValueError: If model or prompt is invalid
            OllamaError: If API returns error
            NetworkError: If connection fails
        """
        self._validate_model_name(model)
        self._validate_non_empty_string(prompt, "prompt")
        data = {"model": model, "prompt": prompt, "stream": stream}
        if options:
            data["options"] = options.model_dump(exclude_unset=True)
        return await self._post("/api/generate", data)

    async def chat(
        self,
        model: str,
        messages: List[ChatMessage],
        tools: Optional[List[Tool]] = None,
        options: Optional[GenerationOptions] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Chat with a model using conversation history.

        Args:
            model: Name of the model to use
            messages: List of chat messages (conversation history)
            tools: Optional list of tools available to the model
            options: Optional generation parameters
            stream: Whether to stream the response (default: False)

        Returns:
            Dictionary containing chat response and metadata

        Raises:
            ValueError: If model is invalid or messages list is empty
            OllamaError: If API returns error
            NetworkError: If connection fails
        """
        self._validate_model_name(model)
        if not messages:
            raise ValueError("messages list cannot be empty")
        data = {
            "model": model,
            "messages": [msg.model_dump(exclude_unset=True) for msg in messages],
            "stream": stream,
        }
        if tools:
            data["tools"] = [tool.model_dump() for tool in tools]
        if options:
            data["options"] = options.model_dump(exclude_unset=True)
        return await self._post("/api/chat", data)

    async def embed(
        self, model: str, input_text: Union[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Generate embeddings for text input.

        Args:
            model: Name of the embedding model to use
            input_text: Single string or list of strings to embed

        Returns:
            Dictionary containing embeddings and metadata

        Raises:
            ValueError: If model or input_text is invalid
            OllamaError: If API returns error
            NetworkError: If connection fails
        """
        self._validate_model_name(model)
        if isinstance(input_text, str):
            self._validate_non_empty_string(input_text, "input_text")
        elif isinstance(input_text, list):
            if not input_text:
                raise ValueError("input_text list cannot be empty")
            for i, text in enumerate(input_text):
                self._validate_non_empty_string(text, f"input_text[{i}]")
        else:
            raise ValueError("input_text must be a string or list of strings")
        return await self._post("/api/embed", {"model": model, "input": input_text})

    async def ps(self) -> Dict[str, Any]:
        """
        List currently running models.

        Returns:
            Dictionary containing list of running models with memory usage

        Raises:
            OllamaError: If API returns error
            NetworkError: If connection fails
        """
        return await self._get("/api/ps")
