# AgentCore Gateway

A gateway service that routes agent requests to MCP servers running on AgentCore runtime.

## Architecture

```
┌─────────────────┐
│  Agent Runtime  │
│  (QNA Agent)    │
└────────┬────────┘
         │
         │ Invokes via Gateway
         ▼
┌─────────────────┐
│ AgentCore       │
│ Gateway         │
│                 │
│ - Routes        │
│ - Authenticates │
│ - Load Balance  │
└────────┬────────┘
         │
         │ JSON-RPC over HTTPS
         │ (AWS SigV4 Auth)
         ▼
┌─────────────────┐
│  MCP Server     │
│  (Memory)       │
│                 │
│ - retrieve      │
│ - store         │
│ - server_info   │
└─────────────────┘
```

## Features

- **Server Registry**: Register multiple MCP servers with the gateway
- **AWS SigV4 Authentication**: Secure communication with AgentCore runtimes
- **JSON-RPC Protocol**: Standard MCP protocol support
- **Tool Discovery**: List available tools on registered servers
- **Error Handling**: Comprehensive error handling and logging
- **SSE Support**: Handles Server-Sent Events response format

## Installation

```bash
cd Scripts/AgentCoreGateway
pip install boto3 requests python-dotenv
```

## Configuration

Create a `.env` file:

```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
MCP_MEMORY_SERVER_ARN=arn:aws:bedrock-agentcore:us-east-1:ACCOUNT:runtime/SERVER_ID
```

Or use `gateway_config.json` for server registry.

## Usage

### Basic Usage

```python
from agentcore_gateway import AgentCoreGateway

# Initialize gateway
gateway = AgentCoreGateway(region="us-east-1")

# Register MCP server
gateway.register_server(
    name="memory",
    arn="arn:aws:bedrock-agentcore:us-east-1:ACCOUNT:runtime/SERVER_ID",
    description="Memory server"
)

# List available tools
tools = gateway.list_tools("memory")

# Invoke a tool
result = gateway.invoke_mcp_tool(
    server_name="memory",
    tool_name="retrieve_memory",
    arguments={
        "query": "user preferences",
        "max_results": 5,
        "actor_id": "user123",
        "session_id": "session456"
    }
)
```

### Integration with Agent

```python
from agentcore_gateway import AgentCoreGateway

# In your agent code
gateway = AgentCoreGateway()
gateway.register_server("memory", MCP_SERVER_ARN)

# Retrieve context before processing
memories = gateway.invoke_mcp_tool(
    "memory",
    "retrieve_memory",
    {"query": user_query, "actor_id": actor_id, "session_id": session_id}
)

# Process with agent...

# Store interaction after processing
gateway.invoke_mcp_tool(
    "memory",
    "store_interaction",
    {
        "user_msg": user_query,
        "assistant_msg": response,
        "actor_id": actor_id,
        "session_id": session_id
    }
)
```

## Testing

Run the example:

```bash
python agentcore_gateway.py
```

This will:
1. List available tools on the memory server
2. Get server info (health check)
3. Store a test interaction
4. Retrieve memory

## API Reference

### AgentCoreGateway

#### `__init__(region, aws_access_key_id, aws_secret_access_key)`
Initialize the gateway with AWS credentials.

#### `register_server(name, arn, description, tags)`
Register an MCP server with the gateway.

#### `invoke_mcp_tool(server_name, tool_name, arguments, timeout)`
Invoke a tool on a registered MCP server.

#### `list_tools(server_name, timeout)`
List all available tools on a server.

#### `get_server_info(server_name, session_id)`
Get server health and runtime information.

## Troubleshooting

### 403 Forbidden Error

If you get a 403 error, ensure:
1. The MCP server has a resource policy allowing invocation
2. Your IAM credentials have `bedrock-agentcore:InvokeRuntime` permission
3. The server ARN is correct

Apply resource policy:
```bash
cd ../../Servers/agentcore-memory-mcp
python apply_gateway_policy.py
```

### Connection Timeout

- Check network connectivity
- Verify the server is running: `aws bedrock-agentcore list-runtimes`
- Increase timeout parameter

### Invalid Response Format

- Ensure MCP server is using FastMCP with `stateless_http=True`
- Check server logs for errors

## Next Steps

1. Add retry logic with exponential backoff
2. Implement connection pooling
3. Add metrics and monitoring
4. Support multiple regions
5. Add caching layer for frequently accessed data
