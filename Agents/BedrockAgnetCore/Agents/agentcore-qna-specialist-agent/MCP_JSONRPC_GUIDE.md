# MCP Memory Integration Guide - JSON-RPC Protocol

## Overview

This guide explains how the QNA Specialist Agent integrates with the MCP Memory Server using JSON-RPC over HTTP with AWS SigV4 authentication.

## Architecture

```
┌─────────────────────────┐
│  QNA Specialist Agent   │
│  (03_agentcore_mcp_     │
│   memory.py)            │
└───────────┬─────────────┘
            │
            │ JSON-RPC over HTTPS
            │ (AWS SigV4 Auth)
            │
            ▼
┌─────────────────────────┐
│  MCP Memory Server      │
│  (FastMCP)              │
│                         │
│  Tools:                 │
│  - retrieve_memory      │
│  - store_interaction    │
│  - server_info          │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  AgentCore Memory       │
│  (AWS Bedrock)          │
└─────────────────────────┘
```

## How It Works

### 1. Connection Setup

The agent connects to the MCP server using:
- **Protocol**: JSON-RPC 2.0 over HTTPS
- **Authentication**: AWS SigV4 (using boto3 credentials)
- **Endpoint**: `https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT`

```python
from urllib.parse import quote
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

# Build endpoint URL
encoded_arn = quote(server_arn, safe='')
invoke_url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"

# Get AWS credentials
session = boto3.Session()
credentials = session.get_credentials()
```

### 2. Making JSON-RPC Calls

All MCP tool calls use the JSON-RPC 2.0 protocol:

```python
payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "retrieve_memory",
        "arguments": {
            "query": "user preferences",
            "max_results": 5,
            "actor_id": "user-123",
            "session_id": "session-456"
        }
    }
}
```

### 3. AWS SigV4 Authentication

Each request is signed with AWS SigV4:

```python
request = AWSRequest(method="POST", url=invoke_url, data=body, headers=headers)
SigV4Auth(credentials, "bedrock-agentcore", region).add_auth(request)

response = requests.post(invoke_url, headers=dict(request.headers), data=body)
```

### 4. Response Parsing

The MCP server returns responses in SSE (Server-Sent Events) format:

```
data: {"jsonrpc":"2.0","id":1,"result":{...}}

```

The client parses this format:

```python
# Handle SSE format
if resp_text.startswith("data:"):
    data_lines = []
    for line in resp_text.splitlines():
        if not line.strip():
            break
        if line.startswith("data:"):
            data_lines.append(line[len("data:"):].lstrip())
    resp_text = "\n".join(data_lines)

resp_json = json.loads(resp_text)
```

## MCP Tools

### retrieve_memory

Retrieves relevant memories for a given query.

**Input:**
```json
{
    "query": "string",
    "max_results": 5,
    "actor_id": "string",
    "session_id": "string"
}
```

**Output:**
```json
{
    "data": {
        "items": [
            {
                "memory_index": 1,
                "strategy": "GeneralStore",
                "content": "User prefers vegetarian food",
                "relevance": 0.95
            }
        ]
    },
    "metadata": {
        "memory_id": "...",
        "actor_id": "...",
        "count": 1
    }
}
```

### store_interaction

Stores a user-assistant interaction.

**Input:**
```json
{
    "user_msg": "string",
    "assistant_msg": "string",
    "actor_id": "string",
    "session_id": "string"
}
```

**Output:**
```json
{
    "data": {
        "stored": true
    },
    "metadata": {
        "memory_id": "...",
        "actor_id": "...",
        "session_id": "..."
    }
}
```

## Configuration

### Environment Variables

```bash
# MCP Memory Server ARN
MCP_MEMORY_SERVER_ARN="arn:aws:bedrock-agentcore:us-east-1:ACCOUNT:runtime/SERVER-ID"

# AWS Region
AWS_REGION="us-east-1"

# AWS Credentials (from boto3 session)
# Can be set via:
# - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
# - AWS credentials file (~/.aws/credentials)
# - IAM role (when running on AWS)
```

### Dependencies

```toml
dependencies = [
    "boto3>=1.35.0",
    "botocore>=1.35.0",
    "requests>=2.32.0",
    "bedrock-agentcore>=1.0.7",
]
```

## Complete Example

```python
import json
import itertools
from urllib.parse import quote
import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

_jsonrpc_id = itertools.count(1)

class MCPMemoryClient:
    """Client for interacting with MCP Memory Server via JSON-RPC"""
    
    def __init__(self, server_arn: str, region: str = "us-east-1"):
        self.server_arn = server_arn
        self.region = region
        
        # Build the invocation URL
        encoded_arn = quote(server_arn, safe='')
        self.invoke_url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
        
        # Get AWS credentials
        session = boto3.Session()
        self.credentials = session.get_credentials()
    
    def _jsonrpc_call(self, method: str, params: dict, timeout: float = 30.0):
        """Make a JSON-RPC call to the MCP server"""
        payload = {
            "jsonrpc": "2.0",
            "id": next(_jsonrpc_id),
            "method": method,
            "params": params,
        }
        body = json.dumps(payload).encode("utf-8")
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        
        # Create and sign the request
        request = AWSRequest(method="POST", url=self.invoke_url, data=body, headers=headers)
        SigV4Auth(self.credentials, "bedrock-agentcore", self.region).add_auth(request)
        
        # Execute the request
        response = requests.post(
            self.invoke_url,
            headers=dict(request.headers),
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
    
    async def retrieve_memory(self, query: str, actor_id: str, session_id: str, max_results: int = 5):
        """Retrieve memories from MCP server"""
        result = self._jsonrpc_call(
            "tools/call",
            {
                "name": "retrieve_memory",
                "arguments": {
                    "query": query,
                    "max_results": max_results,
                    "actor_id": actor_id,
                    "session_id": session_id
                }
            }
        )
        
        # Parse the tool response
        content = result.get("structuredContent", {}).get("result", {}).get("content", [{}])
        if content:
            text = content[0].get("text", "{}")
            data = json.loads(text) if isinstance(text, str) else text
            return data.get("data", {}).get("items", [])
        
        return []
```

## Testing

Run the test suite to verify the integration:

```bash
cd Agents/agentcore-qna-specialist-agent
python test_mcp_integration.py
```

## Deployment

1. **Deploy the agent:**
```bash
agentcore deploy
```

2. **Launch with environment variables:**
```bash
agentcore launch \
  --env GROQ_API_KEY='your_key' \
  --env MCP_MEMORY_SERVER_ARN="arn:aws:bedrock-agentcore:us-east-1:ACCOUNT:runtime/SERVER-ID"
```

3. **Invoke the agent:**
```bash
agentcore invoke \
  --prompt "What is roaming activation?" \
  --actor-id "user-123" \
  --session-id "session-456"
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'boto3'"

**Solution:** Install dependencies:
```bash
pip install boto3 botocore requests
```

### Issue: "Unable to locate credentials"

**Solution:** Configure AWS credentials:
```bash
aws configure
```

### Issue: "403 Forbidden"

**Solution:** Verify your AWS credentials have permission to invoke the MCP server.

## References

- [AWS SigV4 Signing](https://docs.aws.amazon.com/general/latest/gr/signature-version-4.html)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [MCP Protocol](https://modelcontextprotocol.io/)
