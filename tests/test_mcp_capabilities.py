"""
Test script to demonstrate new MCP Ollama capabilities:
- Resources support
- Prompts support  
- Direct code execution
"""

import asyncio
from src.mcp_ollama_python.server import OllamaMCPServer
from src.mcp_ollama_python.ollama_client import OllamaClient


async def test_resources():
    """Test resource listing and reading"""
    print("\n" + "="*60)
    print("TESTING RESOURCES SUPPORT")
    print("="*60)
    
    server = OllamaMCPServer()
    
    # List resources
    print("\n1. Listing available resources:")
    resources = await server.handle_list_resources()
    for resource in resources["resources"]:
        print(f"   - {resource['name']}: {resource['uri']}")
        print(f"     {resource['description']}")
    
    # Read a resource
    print("\n2. Reading 'ollama://config' resource:")
    config = await server.handle_read_resource("ollama://config")
    print(f"   {config['contents'][0]['text']}")


async def test_prompts():
    """Test prompt listing and retrieval"""
    print("\n" + "="*60)
    print("TESTING PROMPTS SUPPORT")
    print("="*60)
    
    server = OllamaMCPServer()
    
    # List prompts
    print("\n1. Listing available prompts:")
    prompts = await server.handle_list_prompts()
    for prompt in prompts["prompts"]:
        print(f"   - {prompt['name']}: {prompt['description']}")
    
    # Get a specific prompt
    print("\n2. Getting 'hello_world' prompt for Python:")
    prompt = await server.handle_get_prompt("hello_world", {"language": "Python"})
    print(f"   Description: {prompt['description']}")
    print(f"   Prompt text:\n{prompt['messages'][0]['content']['text']}")


async def test_execute_tool():
    """Test direct code execution"""
    print("\n" + "="*60)
    print("TESTING EXECUTE TOOL")
    print("="*60)
    
    server = OllamaMCPServer()
    
    # Test 1: Execute provided code
    print("\n1. Executing provided Python code:")
    code = 'print("Hello World from MCP Ollama!")'
    result = await server.handle_call_tool("ollama_execute", {
        "code": code,
        "language": "python"
    })
    print(f"   Code: {code}")
    print(f"   Output: {result['content'][0]['text']}")
    
    # Test 2: Generate and execute code
    print("\n2. Generating and executing code with AI:")
    print("   Prompt: 'print hello world'")
    result = await server.handle_call_tool("ollama_execute", {
        "generate": True,
        "prompt": "print hello world",
        "language": "python",
        "model": "llama3.1"
    })
    print(f"   Result: {result['content'][0]['text'][:200]}...")


async def test_chat_with_prompt():
    """Test using prompts with chat"""
    print("\n" + "="*60)
    print("TESTING CHAT WITH PROMPTS")
    print("="*60)
    
    server = OllamaMCPServer()
    
    # Get the explain_lora prompt
    print("\n1. Using 'explain_lora' prompt with chat:")
    prompt = await server.handle_get_prompt("explain_lora", {"detail_level": "basic"})
    prompt_text = prompt['messages'][0]['content']['text']
    
    # Use it with chat
    result = await server.handle_call_tool("ollama_chat", {
        "model": "llama3.1",
        "messages": [
            {"role": "user", "content": prompt_text}
        ]
    })
    
    print(f"   Prompt: {prompt_text[:100]}...")
    print(f"   Response: {result['content'][0]['text'][:300]}...")


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("MCP OLLAMA - NEW CAPABILITIES TEST")
    print("="*60)
    
    try:
        await test_resources()
        await test_prompts()
        await test_execute_tool()
        await test_chat_with_prompt()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
