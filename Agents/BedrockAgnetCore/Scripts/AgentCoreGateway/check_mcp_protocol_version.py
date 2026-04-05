#!/usr/bin/env python3
"""
Check MCP Protocol Version

This script checks what MCP protocol version your server supports.
Supported versions: 2025-06-18 and 2025-03-26
"""

import os
import json
import itertools
from typing import Dict, Any
from urllib.parse import quote

import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from dotenv import load_dotenv

load_dotenv()

# Configuration
MCP_SERVER_ARN = os.getenv(
    "MCP_MEMORY_SERVER_ARN",
    "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD"
)
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# JSON-RPC ID counter
_jsonrpc_id = itertools.count(1)

# Supported MCP versions
SUPPORTED_VERSIONS = ["2025-06-18", "2025-03-26"]


def make_mcp_request(method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make a request to the MCP server"""
    
    # Initialize AWS session
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        session = boto3.Session(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
    else:
        session = boto3.Session(region_name=AWS_REGION)
    
    credentials = session.get_credentials()
    
    if not credentials:
        raise ValueError("AWS credentials required")
    
    # Build invocation URL
    encoded_arn = quote(MCP_SERVER_ARN, safe='')
    invoke_url = f"https://bedrock-agentcore.{AWS_REGION}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
    
    # Build JSON-RPC payload
    payload = {
        "jsonrpc": "2.0",
        "id": next(_jsonrpc_id),
        "method": method,
        "params": params or {}
    }
    
    body = json.dumps(payload).encode("utf-8")
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    # Sign request
    request = AWSRequest(method="POST", url=invoke_url, data=body, headers=headers)
    SigV4Auth(credentials, "bedrock-agentcore", AWS_REGION).add_auth(request)
    
    # Execute
    response = requests.post(
        invoke_url,
        headers=dict(request.headers),
        data=body,
        timeout=30.0
    )
    
    return {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "text": response.text,
        "ok": response.ok
    }


def parse_response(response_text: str) -> Dict[str, Any]:
    """Parse MCP response (handles SSE format)"""
    resp_text = response_text.strip()
    
    # Handle SSE format
    if resp_text.startswith("data:"):
        data_lines = []
        for line in resp_text.splitlines():
            if not line.strip():
                break
            if line.startswith("data:"):
                data_lines.append(line[len("data:"):].lstrip())
        resp_text = "\n".join(data_lines)
    
    return json.loads(resp_text)


def check_protocol_version():
    """Check MCP protocol version"""
    print("="*80)
    print("MCP PROTOCOL VERSION CHECKER")
    print("="*80)
    print(f"\nServer ARN: {MCP_SERVER_ARN}")
    print(f"Region: {AWS_REGION}")
    print(f"\nSupported versions: {', '.join(SUPPORTED_VERSIONS)}")
    print()
    
    # Method 1: Check initialize response
    print("-"*80)
    print("Method 1: Check 'initialize' method")
    print("-"*80)
    
    try:
        result = make_mcp_request("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {
                "name": "version-checker",
                "version": "1.0.0"
            }
        })
        
        if result["ok"]:
            resp_json = parse_response(result["text"])
            
            if "result" in resp_json:
                result_data = resp_json["result"]
                
                # Check for protocol version in response
                protocol_version = result_data.get("protocolVersion")
                server_info = result_data.get("serverInfo", {})
                capabilities = result_data.get("capabilities", {})
                
                print("✓ Initialize successful!")
                print(f"\nServer Response:")
                print(f"  Protocol Version: {protocol_version}")
                print(f"  Server Name: {server_info.get('name', 'N/A')}")
                print(f"  Server Version: {server_info.get('version', 'N/A')}")
                print(f"  Capabilities: {json.dumps(capabilities, indent=4)}")
                
                if protocol_version in SUPPORTED_VERSIONS:
                    print(f"\n✓ Server supports MCP protocol version: {protocol_version}")
                else:
                    print(f"\n⚠ Server version {protocol_version} may not be supported")
                    print(f"  Supported versions: {', '.join(SUPPORTED_VERSIONS)}")
                
                return protocol_version
            else:
                print("⚠ No 'result' in response")
                print(f"Response: {json.dumps(resp_json, indent=2)}")
        else:
            print(f"✗ Request failed: HTTP {result['status_code']}")
            print(f"Response: {result['text'][:200]}")
            
    except Exception as e:
        print(f"✗ Initialize method failed: {e}")
    
    # Method 2: Check server_info tool
    print("\n" + "-"*80)
    print("Method 2: Check 'server_info' tool")
    print("-"*80)
    
    try:
        result = make_mcp_request("tools/call", {
            "name": "server_info",
            "arguments": {
                "session_id": "version-check"
            }
        })
        
        if result["ok"]:
            resp_json = parse_response(result["text"])
            
            if "result" in resp_json:
                print("✓ server_info call successful!")
                print(f"\nServer Info Response:")
                print(json.dumps(resp_json["result"], indent=2))
            else:
                print("⚠ No 'result' in response")
        else:
            print(f"✗ Request failed: HTTP {result['status_code']}")
            
    except Exception as e:
        print(f"✗ server_info method failed: {e}")
    
    # Method 3: Check response headers
    print("\n" + "-"*80)
    print("Method 3: Check Response Headers")
    print("-"*80)
    
    try:
        result = make_mcp_request("tools/list", {})
        
        if result["ok"]:
            headers = result["headers"]
            
            print("Response Headers:")
            for key, value in headers.items():
                if "mcp" in key.lower() or "protocol" in key.lower() or "version" in key.lower():
                    print(f"  {key}: {value}")
            
            # Check content-type
            content_type = headers.get("content-type", "")
            print(f"\nContent-Type: {content_type}")
            
            if "text/event-stream" in content_type:
                print("✓ Server uses SSE (Server-Sent Events) format")
            elif "application/json" in content_type:
                print("✓ Server uses JSON format")
                
    except Exception as e:
        print(f"✗ Header check failed: {e}")
    
    # Method 4: Check your server code
    print("\n" + "-"*80)
    print("Method 4: Check Server Code")
    print("-"*80)
    
    server_file = "Servers/agentcore-memory-mcp/memory_mcp_server.py"
    
    try:
        with open(server_file, 'r') as f:
            content = f.read()
            
        print(f"Checking: {server_file}")
        
        # Look for FastMCP initialization
        if "FastMCP" in content:
            print("✓ Server uses FastMCP")
            
            # Check for version specification
            if "protocol_version" in content.lower():
                print("✓ Server specifies protocol version")
                # Extract the line
                for line in content.splitlines():
                    if "protocol_version" in line.lower():
                        print(f"  {line.strip()}")
            else:
                print("⚠ No explicit protocol version in code")
                print("  Server likely uses FastMCP default version")
        
        # Check FastMCP import
        if "from mcp.server.fastmcp import FastMCP" in content:
            print("✓ FastMCP imported correctly")
        
        # Check transport
        if "stateless_http=True" in content:
            print("✓ Server uses stateless HTTP (required for AgentCore)")
        
        if 'transport="streamable-http"' in content:
            print("✓ Server uses streamable-http transport")
            
    except FileNotFoundError:
        print(f"⚠ Could not find server file: {server_file}")
    except Exception as e:
        print(f"✗ Error reading server file: {e}")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    print("""
To ensure compatibility with AgentCore Gateway:

1. Your MCP server should support protocol version: 2025-06-18 or 2025-03-26

2. Check your FastMCP version:
   pip show fastmcp

3. Update FastMCP if needed:
   pip install --upgrade fastmcp

4. In your server code (memory_mcp_server.py), ensure:
   - FastMCP is initialized with stateless_http=True
   - Transport is set to "streamable-http"
   
   Example:
   mcp = FastMCP("agentcore_memory_mcp", host="0.0.0.0", stateless_http=True)
   mcp.run(transport="streamable-http")

5. If you need to specify protocol version explicitly:
   mcp = FastMCP(
       "agentcore_memory_mcp",
       host="0.0.0.0",
       stateless_http=True,
       protocol_version="2025-06-18"  # Add this if needed
   )
    """)
    
    print("="*80)


def check_fastmcp_version():
    """Check installed FastMCP version"""
    print("\n" + "="*80)
    print("FASTMCP VERSION CHECK")
    print("="*80)
    
    try:
        import mcp
        print(f"✓ MCP package installed")
        
        # Try to get version
        if hasattr(mcp, '__version__'):
            print(f"  Version: {mcp.__version__}")
        else:
            print("  Version: Unknown (no __version__ attribute)")
        
        # Check FastMCP
        try:
            from mcp.server.fastmcp import FastMCP
            print(f"✓ FastMCP available")
            
            # Check if FastMCP has protocol_version parameter
            import inspect
            sig = inspect.signature(FastMCP.__init__)
            params = list(sig.parameters.keys())
            
            print(f"  FastMCP parameters: {', '.join(params)}")
            
            if 'protocol_version' in params:
                print("  ✓ Supports protocol_version parameter")
            else:
                print("  ⚠ No protocol_version parameter (may use default)")
                
        except ImportError:
            print("✗ FastMCP not available")
            
    except ImportError:
        print("✗ MCP package not installed")
        print("\nInstall with: pip install fastmcp")
    
    print("="*80)


if __name__ == "__main__":
    check_fastmcp_version()
    print()
    check_protocol_version()
