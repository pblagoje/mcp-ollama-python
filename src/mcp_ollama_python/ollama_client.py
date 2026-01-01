"""
Ollama HTTP client wrapper
"""

import os
import httpx
from typing import Any, Dict, List, Optional, Union
import json
from .models import GenerationOptions, ChatMessage, Tool


class OllamaClient:
    """HTTP client for Ollama API"""

    def __init__(self, host: Optional[str] = None, api_key: Optional[str] = None):
        self.host = host or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        self.api_key = api_key or os.getenv("OLLAMA_API_KEY")

        # Create httpx client
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.client = httpx.AsyncClient(
            base_url=self.host,
            headers=headers,
            timeout=300.0,  # 5 minute timeout
            follow_redirects=True  # Follow HTTP redirects (301, 302, etc.)
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def _get(self, endpoint: str) -> Dict[str, Any]:
        """Make a GET request to Ollama API"""
        try:
            response = await self.client.get(endpoint)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"Ollama API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Failed to connect to Ollama: {str(e)}")

    async def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request to Ollama API"""
        try:
            response = await self.client.post(endpoint, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"Ollama API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Failed to connect to Ollama: {str(e)}")

    async def list(self) -> Dict[str, Any]:
        """List all available models"""
        return await self._get("/api/tags")

    async def show(self, model: str) -> Dict[str, Any]:
        """Show model information"""
        return await self._post("/api/show", {"name": model})

    async def pull(self, model: str) -> Dict[str, Any]:
        """Pull a model"""
        return await self._post("/api/pull", {"name": model})

    async def push(self, model: str) -> Dict[str, Any]:
        """Push a model"""
        return await self._post("/api/push", {"name": model})

    async def copy(self, source: str, destination: str) -> Dict[str, Any]:
        """Copy a model"""
        return await self._post("/api/copy", {"source": source, "destination": destination})

    async def delete(self, model: str) -> Dict[str, Any]:
        """Delete a model"""
        return await self._post("/api/delete", {"name": model})

    async def create(self, name: str, modelfile: str, stream: bool = False) -> Dict[str, Any]:
        """Create a model from Modelfile"""
        data = {"name": name, "modelfile": modelfile}
        if stream:
            data["stream"] = True
        return await self._post("/api/create", data)

    async def generate(self, model: str, prompt: str, options: Optional[GenerationOptions] = None, stream: bool = False) -> Dict[str, Any]:
        """Generate text"""
        data = {"model": model, "prompt": prompt, "stream": stream}
        if options:
            data["options"] = options.model_dump(exclude_unset=True)
        return await self._post("/api/generate", data)

    async def chat(self, model: str, messages: List[ChatMessage], tools: Optional[List[Tool]] = None, options: Optional[GenerationOptions] = None, stream: bool = False) -> Dict[str, Any]:
        """Chat with a model"""
        data = {
            "model": model,
            "messages": [msg.model_dump(exclude_unset=True) for msg in messages],
            "stream": stream
        }
        if tools:
            data["tools"] = [tool.model_dump() for tool in tools]
        if options:
            data["options"] = options.model_dump(exclude_unset=True)
        return await self._post("/api/chat", data)

    async def embed(self, model: str, input: Union[str, List[str]]) -> Dict[str, Any]:
        """Generate embeddings"""
        return await self._post("/api/embed", {"model": model, "input": input})

    async def ps(self) -> Dict[str, Any]:
        """List running models"""
        return await self._get("/api/ps")
