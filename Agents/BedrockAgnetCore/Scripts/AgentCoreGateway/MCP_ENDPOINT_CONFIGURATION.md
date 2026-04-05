# MCP Endpoint Configuration for AgentCore Runtime

## Your MCP Server Details

### Server Information
- **Server Name:** agentcore_memory_mcp_server
- **Server ID:** R4jmV6ERZD
- **Account:** 662403250828
- **Region:** us-east-1

### Full ARN
```
arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD
```

## MCP Endpoint URL

For AgentCore Gateway integration, use this endpoint:

### Option 1: Runtime Endpoint (Recommended)
```
https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD/runtime-endpoint/DEFAULT/invocations
```

### Option 2: Direct Invocation Endpoint
```
https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn%3Aaws%3Abedrock-agentcore%3Aus-east-1%3A662403250828%3Aruntime%2Fagentcore_memory_mcp_server-R4jmV6ERZD/invocations?qualifier=DEFAULT
```

**Note:** Option 2 uses URL-encoded ARN (`%3A` for `:`, `%2F` for `/`)

## Gateway Target Configuration

### Complete Target Definition

```json
{
  "targetName": "memory-mcp-server",
  "targetType": "MCP_SERVER",
  "description": "AgentCore Memory MCP Server for storing and retrieving conversation context",
  "endpoint": {
    "url": "https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD/runtime-endpoint/DEFAULT/invocations",
    "protocol": "MCP",
    "protocolVersion": "2025-06-18"
  },
  "authentication": {
    "type": "AWS_SIGV4",
    "service": "bedrock-agentcore",
    "region": "us-east-1"
  },
  "resourcePolicy": {
    "required": true,
    "status": "pending"
  },
  "tools": [
    {
      "name": "retrieve_memory",
      "description": "Retrieve long-term memory records for an actor",
      "inputSchema": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "Semantic search string"
          },
          "max_results": {
            "type": "integer",
            "description": "Number of results (1-100)",
            "default": 10
          },
          "actor_id": {
            "type": "string",
            "description": "Actor to search within"
          },
          "session_id": {
            "type": "string",
            "description": "Optional session identifier"
          }
        },
        "required": ["query", "actor_id"]
      }
    },
    {
      "name": "store_interaction",
      "description": "Persist a user/assistant turn into AgentCore Memory",
      "inputSchema": {
        "type": "object",
        "properties": {
          "user_msg": {
            "type": "string",
            "description": "End-user text"
          },
          "assistant_msg": {
            "type": "string",
            "description": "Assistant text"
          },
          "actor_id": {
            "type": "string",
            "description": "Actor identifier"
          },
          "session_id": {
            "type": "string",
            "description": "Session identifier"
          }
        },
        "required": ["user_msg", "assistant_msg", "actor_id"]
      }
    },
    {
      "name": "server_info",
      "description": "Return MCP server runtime details (health/debug)",
      "inputSchema": {
        "type": "object",
        "properties": {
          "session_id": {
            "type": "string",
            "description": "Correlation id for tracing"
          }
        },
        "required": ["session_id"]
      }
    }
  ],
  "metadata": {
    "serverArn": "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD",
    "deploymentType": "direct_code_deploy",
    "runtimeType": "PYTHON_3_13",
    "memoryId": "MyAgentMemory20260211160131-gMGdB67nD0"
  }
}
```

## Integration Provider Template

### For AWS Console / CLI

If you're configuring this through AWS Console or CLI, use this template:

```yaml
TargetName: memory-mcp-server
TargetType: MCP_SERVER
Description: AgentCore Memory MCP Server

Endpoint:
  URL: https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD/runtime-endpoint/DEFAULT/invocations
  Protocol: MCP
  ProtocolVersion: 2025-06-18

Authentication:
  Type: AWS_SIGV4
  Service: bedrock-agentcore
  Region: us-east-1

ResourceArn: arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD
```

## Terraform Configuration

```hcl
resource "aws_bedrock_agentcore_gateway_target" "memory_mcp" {
  target_name = "memory-mcp-server"
  target_type = "MCP_SERVER"
  description = "AgentCore Memory MCP Server"

  endpoint {
    url              = "https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD/runtime-endpoint/DEFAULT/invocations"
    protocol         = "MCP"
    protocol_version = "2025-06-18"
  }

  authentication {
    type    = "AWS_SIGV4"
    service = "bedrock-agentcore"
    region  = "us-east-1"
  }

  resource_arn = "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD"

  tags = {
    Environment = "production"
    Service     = "memory"
    Protocol    = "MCP"
  }
}
```

## CloudFormation Template

```yaml
Resources:
  MemoryMCPTarget:
    Type: AWS::BedrockAgentCore::GatewayTarget
    Properties:
      TargetName: memory-mcp-server
      TargetType: MCP_SERVER
      Description: AgentCore Memory MCP Server
      Endpoint:
        URL: https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD/runtime-endpoint/DEFAULT/invocations
        Protocol: MCP
        ProtocolVersion: 2025-06-18
      Authentication:
        Type: AWS_SIGV4
        Service: bedrock-agentcore
        Region: us-east-1
      ResourceArn: arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD
      Tags:
        - Key: Environment
          Value: production
        - Key: Service
          Value: memory
```

## Python SDK Configuration

```python
import boto3

client = boto3.client('bedrock-agentcore', region_name='us-east-1')

response = client.create_gateway_target(
    targetName='memory-mcp-server',
    targetType='MCP_SERVER',
    description='AgentCore Memory MCP Server',
    endpoint={
        'url': 'https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD/runtime-endpoint/DEFAULT/invocations',
        'protocol': 'MCP',
        'protocolVersion': '2025-06-18'
    },
    authentication={
        'type': 'AWS_SIGV4',
        'service': 'bedrock-agentcore',
        'region': 'us-east-1'
    },
    resourceArn='arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD'
)

print(f"Target created: {response['targetId']}")
```

## Key Configuration Fields

### Required Fields

1. **Target Name**
   ```
   memory-mcp-server
   ```

2. **Target Type**
   ```
   MCP_SERVER
   ```

3. **Endpoint URL**
   ```
   https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD/runtime-endpoint/DEFAULT/invocations
   ```

4. **Protocol**
   ```
   MCP
   ```

5. **Protocol Version**
   ```
   2025-06-18
   ```
   (or `2025-03-26` if using older version)

6. **Authentication Type**
   ```
   AWS_SIGV4
   ```

7. **Service**
   ```
   bedrock-agentcore
   ```

8. **Region**
   ```
   us-east-1
   ```

### Optional Fields

9. **Description**
   ```
   AgentCore Memory MCP Server for storing and retrieving conversation context
   ```

10. **Resource ARN**
    ```
    arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD
    ```

11. **Tags**
    ```json
    {
      "Environment": "production",
      "Service": "memory",
      "Protocol": "MCP"
    }
    ```

## Endpoint URL Formats

### Format 1: Runtime Endpoint (Recommended)
```
https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{arn}/runtime-endpoint/{qualifier}/invocations
```

**Example:**
```
https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD/runtime-endpoint/DEFAULT/invocations
```

### Format 2: Direct Invocation (URL-encoded)
```
https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{url-encoded-arn}/invocations?qualifier={qualifier}
```

**Example:**
```
https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn%3Aaws%3Abedrock-agentcore%3Aus-east-1%3A662403250828%3Aruntime%2Fagentcore_memory_mcp_server-R4jmV6ERZD/invocations?qualifier=DEFAULT
```

## URL Encoding Reference

When using Format 2, encode these characters:
- `:` → `%3A`
- `/` → `%2F`

**Original ARN:**
```
arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD
```

**URL-Encoded ARN:**
```
arn%3Aaws%3Abedrock-agentcore%3Aus-east-1%3A662403250828%3Aruntime%2Fagentcore_memory_mcp_server-R4jmV6ERZD
```

## Testing the Endpoint

### Using curl

```bash
# Set variables
ENDPOINT="https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD/runtime-endpoint/DEFAULT/invocations"

# Test with tools/list
aws bedrock-agentcore invoke-runtime \
  --runtime-arn "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD" \
  --payload '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
  --region us-east-1 \
  response.json

cat response.json
```

### Using Python

```python
from Scripts.AgentCoreGateway.agentcore_gateway import AgentCoreGateway

gateway = AgentCoreGateway(region="us-east-1")
gateway.register_server(
    name="memory",
    arn="arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD"
)

# Test
tools = gateway.list_tools("memory")
print(f"Found {len(tools)} tools")
```

## Resource Policy Requirement

⚠️ **Important:** Before the gateway can access your MCP server, you must apply a resource policy.

See: `apply_policy_manual.md` for instructions.

The policy must allow:
```json
{
  "Effect": "Allow",
  "Principal": {
    "Service": "bedrock-agentcore.amazonaws.com"
  },
  "Action": [
    "bedrock-agentcore:InvokeRuntime",
    "bedrock-agentcore:InvokeAgentRuntime"
  ],
  "Resource": "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD"
}
```

## Quick Copy-Paste Values

### For Gateway Configuration Form

**Target Name:**
```
memory-mcp-server
```

**Target Type:**
```
MCP_SERVER
```

**MCP Endpoint URL:**
```
https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD/runtime-endpoint/DEFAULT/invocations
```

**Protocol:**
```
MCP
```

**Protocol Version:**
```
2025-06-18
```

**Authentication Type:**
```
AWS_SIGV4
```

**Service:**
```
bedrock-agentcore
```

**Region:**
```
us-east-1
```

**Resource ARN:**
```
arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD
```

## Troubleshooting

### 403 Forbidden
- **Cause:** Resource policy not applied
- **Solution:** See `apply_policy_manual.md`

### 404 Not Found
- **Cause:** Incorrect endpoint URL or ARN
- **Solution:** Verify ARN and endpoint format

### Connection Timeout
- **Cause:** Server not running or network issue
- **Solution:** Check server status with `aws bedrock-agentcore list-runtimes`

### Protocol Version Mismatch
- **Cause:** Server uses different protocol version
- **Solution:** Run `python check_mcp_protocol_version.py`

## Next Steps

1. Copy the endpoint URL above
2. Configure your gateway target with these values
3. Apply resource policy (see `apply_policy_manual.md`)
4. Test connection (see `test_gateway.py`)

## Support Files

- `gateway_target_config_mcp.json` - JSON configuration
- `apply_policy_manual.md` - Resource policy guide
- `test_gateway.py` - Test script
- `agentcore_gateway.py` - Python implementation
