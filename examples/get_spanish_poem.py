"""
Get a Spanish poem using local MCP Ollama server with gpt-oss model
"""

import asyncio
import json
from mcp_ollama_python.ollama_client import OllamaClient
from mcp_ollama_python.models import ChatMessage


async def get_spanish_poem():
    """Generate a Spanish poem using gpt-oss model"""
    print("Connecting to Ollama server...")
    client = OllamaClient()

    print("Requesting Spanish poem from gpt-oss model...")

    # Create chat message
    messages = [
        ChatMessage(
            role="user",
            content="Escribe un poema bonito en español sobre la vida, el amor y la esperanza. Hazlo corto pero emotivo.",
        )
    ]

    try:
        # Call Ollama chat API
        result = await client.chat(model="gpt-oss", messages=messages)

        # Extract the response
        if result and "message" in result:
            poem = result["message"].get("content", "")
            print("\n" + "=" * 60)
            print("POEMA EN ESPAÑOL (Spanish Poem)")
            print("=" * 60)
            print(poem)
            print("=" * 60)
            return poem
        else:
            print("Error: No response received")
            print(f"Result: {json.dumps(result, indent=2)}")
            return None
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return None
    finally:
        await client.client.aclose()


if __name__ == "__main__":
    try:
        asyncio.run(get_spanish_poem())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
