"""
Author: Sarvagya Meel
Email: sarvagyameel2@gmail.com
Date: 11/02/26
"""

import asyncio
import os
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    agent_arn = os.getenv('AGENT_ARN','arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp-oaRQGq3VQf')
    bearer_token = os.getenv('BEARER_TOKEN', ' ')
    if not agent_arn or not bearer_token:
        print("Error: AGENT_ARN or BEARER_TOKEN environment variable is not set")
        sys.exit(1)

    encoded_arn = agent_arn.replace(':', '%3A').replace('/', '%2F')
    mcp_url = f"https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
    # headers = {"authorization": f"Bearer {bearer_token}", "Content-Type": "application/json"}
    # print(f"Invoking: {mcp_url}, \nwith headers: {headers}\n")

    async with streamablehttp_client(mcp_url, timeout=120, terminate_on_close=False) as (
            read_stream,
            write_stream,
            _,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tool_result = await session.list_tools()
            print(tool_result)


asyncio.run(main())
