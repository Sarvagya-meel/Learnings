"""
Author: Sarvagya Meel
Email: sarvagyameel2@gmail.com
Date: 11/02/26
"""
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def run_memory_query():
    # 1. Configure the server connection (run via 'uv' or 'python')
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "mcp_server.py"],  # Path to your MCP server file
        env=None
    )

    # print("Connecting to AgentCore Memory MCP Server...")

    # 2. Establish the transport and session
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the protocol handshake
            await session.initialize()

            # 3. Call the 'retrieve_memory' tool
            print("Querying memory for: 'user preferences'...")
            result = await session.call_tool(
                "retrieve_memory",
                arguments={
                    "query": "user preferences about food",
                    "max_results": 2
                }
            )

            # 4. Handle and print the response
            if result.content:
                for item in result.content:
                    print(f"\n--- Memory Found ---\n{item.text}")
            else:
                print("No relevant memories found.")


if __name__ == "__main__":
    try:
        asyncio.run(run_memory_query())
    except Exception as e:
        print(f"Error: {e}")
