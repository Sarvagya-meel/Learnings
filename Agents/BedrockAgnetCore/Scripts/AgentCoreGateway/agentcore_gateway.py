#!/usr/bin/env python3
"""
AgentCore Gateway - Routes agent requests to MCP servers

This gateway acts as a proxy/router that:
1. Receives requests from AgentCore agents
2. Routes them to appropriate MCP servers
3. Handles authentication and authorization
4. Returns responses back to agents

Author: AgentCore Team
Date: 2026-02-20
"""

import os
import json
import logging
import itertools
from typing import Dict, Any, Optional, List
from urllib.parse import quote
from dataclasses import dataclass

import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("agentcore.gateway")

# JSON-RPC ID counter
_jsonrpc_id = itertools.count(1)


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server"""
    name: str
    arn: str
    region: str
    description: str = ""
    tags: List[str] = None


class AgentCoreGateway:
    """Gateway for routing agent requests to MCP servers"""
    
    def __init__(
        self,
        region: str = "us-east-1",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None
    ):
        self.region = region
        
        # Initialize AWS session
        if aws_access_key_id and aws_secret_access_key:
            self.session = boto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region
            )
        else:
            self.session = boto3.Session(region_name=region)
        
        self.credentials = self.session.get_credentials()
        
        if not self.credentials:
            raise ValueError("AWS credentials are required but not found")
        
        # Registry of MCP servers
        self.servers: Dict[str, MCPServerConfig] = {}
        
        logger.info(f"Gateway initialized in region: {region}")
    
    def register_server(
        self,
        name: str,
        arn: str,
        description: str = "",
        tags: List[str] = None
    ):
        """Register an MCP server with the gateway"""
        config = MCPServerConfig(
            name=name,
            arn=arn,
            region=self.region,
            description=description,
            tags=tags or []
        )
        self.servers[name] = config
        logger.info(f"Registered MCP server: {name} -> {arn}")
    
    def _build_invoke_url(self, server_arn: str, qualifier: str = "DEFAULT") -> str:
        """Build the invocation URL for an MCP server"""
        encoded_arn = quote(server_arn, safe='')
        return f"https://bedrock-agentcore.{self.region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier={qualifier}"
    
    def _sign_request(self, url: str, body: bytes, headers: Dict[str, str]) -> Dict[str, str]:
        """Sign a request with AWS SigV4"""
        request = AWSRequest(method="POST", url=url, data=body, headers=headers)
        SigV4Auth(self.credentials, "bedrock-agentcore", self.region).add_auth(request)
        return dict(request.headers)
    
    def invoke_mcp_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        Invoke a tool on an MCP server
        
        Args:
            server_name: Name of the registered MCP server
            tool_name: Name of the tool to invoke
            arguments: Tool arguments
            timeout: Request timeout in seconds
            
        Returns:
            Tool execution result
        """
        if server_name not in self.servers:
            raise ValueError(f"Server '{server_name}' not registered")
        
        server = self.servers[server_name]
        
        # Build JSON-RPC payload
        payload = {
            "jsonrpc": "2.0",
            "id": next(_jsonrpc_id),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        body = json.dumps(payload).encode("utf-8")
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        
        # Build and sign request
        invoke_url = self._build_invoke_url(server.arn)
        signed_headers = self._sign_request(invoke_url, body, headers)
        
        logger.info(f"Invoking {tool_name} on {server_name}")
        
        # Execute request
        response = requests.post(
            invoke_url,
            headers=signed_headers,
            data=body,
            timeout=timeout
        )
        response.raise_for_status()
        
        # Parse response (handle SSE format)
        resp_text = response.text.strip()
        
        if resp_text.startswith("data:"):
            data_lines = []
            for line in resp_text.splitlines():
                if not line.strip():
                    break
                if line.startswith("data:"):
                    data_lines.append(line[len("data:"):].lstrip())
            resp_text = "\n".join(data_lines)
        
        resp_json = json.loads(resp_text)
        
        if resp_json.get("error"):
            raise Exception(f"JSON-RPC error: {resp_json['error']}")
        
        return resp_json.get("result", {})
    
    def list_tools(self, server_name: str, timeout: float = 30.0) -> List[Dict[str, Any]]:
        """
        List available tools on an MCP server
        
        Args:
            server_name: Name of the registered MCP server
            timeout: Request timeout in seconds
            
        Returns:
            List of tool definitions
        """
        if server_name not in self.servers:
            raise ValueError(f"Server '{server_name}' not registered")
        
        server = self.servers[server_name]
        
        # Build JSON-RPC payload for tools/list
        payload = {
            "jsonrpc": "2.0",
            "id": next(_jsonrpc_id),
            "method": "tools/list",
            "params": {}
        }
        
        body = json.dumps(payload).encode("utf-8")
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        
        # Build and sign request
        invoke_url = self._build_invoke_url(server.arn)
        signed_headers = self._sign_request(invoke_url, body, headers)
        
        logger.info(f"Listing tools on {server_name}")
        
        # Execute request
        response = requests.post(
            invoke_url,
            headers=signed_headers,
            data=body,
            timeout=timeout
        )
        response.raise_for_status()
        
        # Parse response
        resp_text = response.text.strip()
        
        if resp_text.startswith("data:"):
            data_lines = []
            for line in resp_text.splitlines():
                if not line.strip():
                    break
                if line.startswith("data:"):
                    data_lines.append(line[len("data:"):].lstrip())
            resp_text = "\n".join(data_lines)
        
        resp_json = json.loads(resp_text)
        
        if resp_json.get("error"):
            raise Exception(f"JSON-RPC error: {resp_json['error']}")
        
        result = resp_json.get("result", {})
        return result.get("tools", [])
    
    def get_server_info(self, server_name: str, session_id: str = "gateway-check") -> Dict[str, Any]:
        """Get server information (health check)"""
        return self.invoke_mcp_tool(
            server_name=server_name,
            tool_name="server_info",
            arguments={"session_id": session_id}
        )


def main():
    """Example usage of the gateway"""
    
    # Configuration
    MCP_SERVER_ARN = os.getenv(
        "MCP_MEMORY_SERVER_ARN",
        "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD"
    )
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    # Initialize gateway
    gateway = AgentCoreGateway(
        region=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    
    # Register MCP memory server
    gateway.register_server(
        name="memory",
        arn=MCP_SERVER_ARN,
        description="AgentCore Memory MCP Server",
        tags=["memory", "storage", "context"]
    )
    
    print("="*80)
    print("AgentCore Gateway - Example Usage")
    print("="*80)
    
    # Test 1: List available tools
    print("\n1. Listing available tools...")
    try:
        tools = gateway.list_tools("memory")
        print(f"✓ Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.get('name')}: {tool.get('description', 'No description')}")
    except Exception as e:
        print(f"✗ Failed to list tools: {e}")
    
    # Test 2: Get server info
    print("\n2. Getting server info...")
    try:
        info = gateway.get_server_info("memory")
        print(f"✓ Server info retrieved:")
        print(json.dumps(info, indent=2))
    except Exception as e:
        print(f"✗ Failed to get server info: {e}")
    
    # Test 3: Store an interaction
    print("\n3. Storing test interaction...")
    try:
        result = gateway.invoke_mcp_tool(
            server_name="memory",
            tool_name="store_interaction",
            arguments={
                "user_msg": "What is AgentCore?",
                "assistant_msg": "AgentCore is AWS's framework for building AI agents.",
                "actor_id": "gateway-test-user",
                "session_id": "gateway-test-session"
            }
        )
        print(f"✓ Interaction stored:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"✗ Failed to store interaction: {e}")
    
    # Test 4: Retrieve memory
    print("\n4. Retrieving memory...")
    try:
        result = gateway.invoke_mcp_tool(
            server_name="memory",
            tool_name="retrieve_memory",
            arguments={
                "query": "AgentCore",
                "max_results": 3,
                "actor_id": "gateway-test-user",
                "session_id": "gateway-test-session"
            }
        )
        print(f"✓ Memory retrieved:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"✗ Failed to retrieve memory: {e}")
    
    print("\n" + "="*80)
    print("Gateway tests completed!")
    print("="*80)


if __name__ == "__main__":
    main()
