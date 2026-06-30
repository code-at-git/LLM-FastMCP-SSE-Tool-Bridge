import json
import asyncio
import sys
import ollama
from fastmcp import Client as MCPClient

# Configuration
OLLAMA_MODEL = "llama3.2:3b"
# Using the exact URL endpoint that worked when you fixed it
MCP_SERVER_URL = "http://127.0.0.1:8080/sse"

class MCPToolBridge:
    """Manages discovery and safe execution for all 8 server tools over SSE."""
    def __init__(self, mcp_session):
        self.mcp = mcp_session

    async def fetch_ollama_tools(self) -> list:
        """Discovers all 8 tools on the server and maps them to Ollama format."""
        tools_list = await self.mcp.list_tools()
        ollama_tools = []
        for t in tools_list:
            # Safely handle inputSchema converting dictionaries
            schema = t.inputSchema
            if hasattr(schema, "model_dump"):
                schema = schema.model_dump()
            elif hasattr(schema, "dict"):
                schema = schema.dict()

            ollama_tools.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": schema,
                },
            })
        return ollama_tools

    async def execute(self, name: str, arguments: dict) -> str:
        """Executes a server tool and safely serializes complex output to strings."""
        try:
            result = await self.mcp.call_tool(name, arguments)
            # FastMCP tools return results inside a 'content' block wrapper
            if hasattr(result, "content"):
                return "".join([block.text for block in result.content if hasattr(block, "text")])
            if isinstance(result, list) and len(result) > 0 and hasattr(result[0], "text"):
                return "".join([block.text for block in result])
            return json.dumps(result) if isinstance(result, (dict, list)) else str(result)
        except Exception as e:
            return json.dumps({"error": f"Tool execution failed: {str(e)}"})


async def run_conversation(mcp_bridge: MCPToolBridge, user_prompt: str):
    """A completely generic, reusable loop handling multiple tool calls per turn."""
    print(f"\n👤 User: {user_prompt}")
    print("-" * 50)
    
    # Auto-discover all available tools directly from the server
    ollama_tools = await mcp_bridge.fetch_ollama_tools()
    messages = [{"role": "user", "content": user_prompt}]

    # Turn 1: Ask Ollama what tools are needed to satisfy the request
    try:
        response = ollama.chat(model=OLLAMA_MODEL, messages=messages, tools=ollama_tools)
    except Exception as e:
        print(f"❌ Ollama Connection Error: {e}")
        return

    messages.append(response["message"])
    tool_calls = response.get("message", {}).get("tool_calls", [])
    
    if not tool_calls:
        print(f"🤖 AI: {response['message']['content']}")
        print("=" * 60)
        return

    # Loop dynamically through any combination of the tools requested by the LLM
    for tool_call in tool_calls:
        name = tool_call["function"]["name"]
        args = tool_call["function"]["arguments"]
        if isinstance(args, str):
            args = json.loads(args)

        print(f"🔧 [Tool Call] -> {name}({args})")
        
        # Execute the tool via our bridge instance
        result_content = await mcp_bridge.execute(name, args)
        print(f"✅ [Server Response] -> {result_content}")

        # Provide the context back to the chat history
        messages.append({
            "role": "tool",
            "content": result_content,
        })

    # Turn 2: Provide the tool execution results back to the LLM for a final synthesis
    try:
        final_response = ollama.chat(model=OLLAMA_MODEL, messages=messages)
        print(f"🤖 AI: {final_response['message']['content']}")
    except Exception as e:
        print(f"❌ Ollama Final Turn Error: {e}")
    print("=" * 60)


async def main():
    print(f"🔌 Connecting to MCP Server via FastMCP Client: {MCP_SERVER_URL}")
    try:
        # Reverted back to the working initialization format from your original script
        async with MCPClient(MCP_SERVER_URL) as session:
            print("🚀 Connected successfully to 'My First MCP Server'!")
            bridge = MCPToolBridge(session)
            
            # Check server tool payload array size
            available = await bridge.fetch_ollama_tools()
            print(f"📦 Successfully mapped all {len(available)} server tools to Ollama.\n")
            print("🤖 Running exactly 8 distinct tool calls in sequence...\n")

            # Call 1: Testing greet tool
            await run_conversation(bridge, "Greet a user named Sarah.")

            # Call 2: Testing add tool
            await run_conversation(bridge, "Add the numbers 350 and 420 together.")

            # Call 3: Testing multiply tool
            await run_conversation(bridge, "Multiply 12.5 by 4.0.")

            # Call 4: Testing get_time tool
            await run_conversation(bridge, "What is the current time right now?")

            # Call 5: Testing get_weather tool
            await run_conversation(bridge, "Check the weather data for Tokyo.")

            # Call 6: Testing save_note tool
            await run_conversation(bridge, "Save a note titled 'Meeting' with the content 'Review product specs at 2 PM'.")

            # Call 7: Testing list_notes tool
            await run_conversation(bridge, "List all my saved notes from the folder.")

            # Call 8: Testing search_users tool
            await run_conversation(bridge, "Search our system for a user named Alice.")

            print("\n🏁 Finished executing all 8 tool workflows successfully!")
                        
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        print(f"Please verify that your server is up and listening on {MCP_SERVER_URL}")

if __name__ == "__main__":
    asyncio.run(main())
