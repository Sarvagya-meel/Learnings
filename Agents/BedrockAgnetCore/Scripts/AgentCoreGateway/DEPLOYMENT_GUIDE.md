# AgentCore Gateway Deployment Guide

## Overview

This guide walks you through deploying and configuring the AgentCore Gateway to enable communication between agents and MCP servers.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        AWS Account                            │
│                                                               │
│  ┌─────────────────┐         ┌──────────────────┐           │
│  │  QNA Agent      │         │  Gateway         │           │
│  │  Runtime        │────────▶│  (Optional)      │           │
│  │                 │         │                  │           │
│  └─────────────────┘         └────────┬─────────┘           │
│         │                              │                     │
│         │ Direct Invocation            │                     │
│         │ (with Gateway lib)           │                     │
│         │                              │                     │
│         ▼                              ▼                     │
│  ┌──────────────────────────────────────────────┐           │
│  │  MCP Memory Server Runtime                   │           │
│  │  ARN: ...runtime/agentcore_memory_mcp_...    │           │
│  │                                               │           │
│  │  Tools:                                       │           │
│  │  - retrieve_memory                            │           │
│  │  - store_interaction                          │           │
│  │  - server_info                                │           │
│  └──────────────────────────────────────────────┘           │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. AWS Account with AgentCore enabled
2. Python 3.9+
3. AWS CLI configured
4. MCP Memory Server deployed (already done in your case)
5. Appropriate IAM permissions

## Step 1: Install Dependencies

```bash
cd Scripts/AgentCoreGateway
pip install -r requirements.txt
```

## Step 2: Configure Environment

Create a `.env` file:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here

# MCP Server Configuration
MCP_MEMORY_SERVER_ARN=arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD

# Optional: Default Actor/Session
DEFAULT_ACTOR_ID=qna-specialist-user
DEFAULT_SESSION_ID=default-session
```

## Step 3: Apply Resource Policies

The MCP server needs a resource policy to allow invocation:

```bash
cd ../../Servers/agentcore-memory-mcp
python apply_gateway_policy.py
```

This creates and attempts to apply a policy that allows:
- The bedrock-agentcore service to invoke the server
- All IAM users/roles in your account to invoke the server

If automatic application fails, follow the manual steps in the script output.

## Step 4: Test the Gateway

```bash
cd ../../Scripts/AgentCoreGateway
python agentcore_gateway.py
```

Expected output:
```
================================================================================
AgentCore Gateway - Example Usage
================================================================================

1. Listing available tools...
✓ Found 3 tools:
  - retrieve_memory: Retrieve long-term memory records for an actor.
  - store_interaction: Persist a user/assistant turn into AgentCore Memory.
  - server_info: Return MCP server runtime details (health/debug).

2. Getting server info...
✓ Server info retrieved:
{
  "structuredContent": {...}
}

3. Storing test interaction...
✓ Interaction stored

4. Retrieving memory...
✓ Memory retrieved
```

## Step 5: Integrate with Your Agent

### Option A: Use Gateway Library (Recommended)

Update your agent file to use the gateway:

```python
# In your agent file (e.g., 03_agentcore_mcp_memory.py)
from Scripts.AgentCoreGateway.agentcore_gateway import AgentCoreGateway

# Initialize gateway
gateway = AgentCoreGateway(
    region=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

gateway.register_server(
    name="memory",
    arn=MCP_MEMORY_SERVER_ARN,
    description="Memory MCP Server"
)

# Use gateway methods
result = gateway.invoke_mcp_tool(
    server_name="memory",
    tool_name="retrieve_memory",
    arguments={...}
)
```

### Option B: Keep Existing Client (Current Approach)

Your current implementation in `03_agentcore_mcp_memory.py` already works well. The gateway provides:
- Centralized server registry
- Easier multi-server management
- Consistent error handling

But your direct client approach is fine for single-server scenarios.

## Step 6: Deploy Updated Agent

If you modified your agent to use the gateway:

```bash
cd ../../Agents/agentcore-qna-specialist-agent

# Update dependencies in pyproject.toml if needed
# Then deploy
bedrock-agentcore deploy
```

## Step 7: Test End-to-End

Test the full flow:

```bash
# Test agent invocation
python test_mcp_integration.py
```

Or use the AWS CLI:

```bash
aws bedrock-agentcore invoke-runtime \
  --runtime-arn arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_qna_agent-LuJi165oYZ \
  --payload '{"prompt": "What is bottle gourd?", "actor_id": "test-user", "session_id": "test-session"}' \
  --region us-east-1
```

## Troubleshooting

### 403 Forbidden Error

**Symptom**: Gateway returns 403 when invoking MCP server

**Solutions**:
1. Verify resource policy is applied to MCP server
2. Check IAM permissions for your credentials
3. Ensure the server ARN is correct
4. Check CloudWatch logs for detailed error messages

```bash
# Check if policy is applied
aws bedrock-agentcore get-runtime-resource-policy \
  --resource-arn $MCP_MEMORY_SERVER_ARN \
  --region us-east-1
```

### Connection Timeout

**Symptom**: Requests timeout after 30 seconds

**Solutions**:
1. Check if MCP server is running:
```bash
aws bedrock-agentcore list-runtimes --region us-east-1
```

2. Increase timeout in gateway:
```python
result = gateway.invoke_mcp_tool(..., timeout=60.0)
```

3. Check server logs in CloudWatch

### Invalid Response Format

**Symptom**: JSON parsing errors or unexpected response format

**Solutions**:
1. Ensure MCP server uses `stateless_http=True`:
```python
# In memory_mcp_server.py
mcp = FastMCP("agentcore_memory_mcp", host=MCP_HOST, stateless_http=True)
```

2. Check server logs for errors
3. Test server directly with curl:
```bash
# Get temporary credentials
aws sts get-session-token

# Test with signed request (use AWS SigV4 signing tool)
```

### Memory Not Persisting

**Symptom**: Stored interactions don't appear in retrieval

**Solutions**:
1. Check if memory ID is correct in server config
2. Verify actor_id and session_id are consistent
3. Check AgentCore Memory service status
4. Review server logs for storage errors

## Monitoring

### CloudWatch Logs

View gateway and server logs:

```bash
# MCP Server logs
aws logs tail /aws/bedrock-agentcore/runtime/agentcore_memory_mcp_server-R4jmV6ERZD \
  --follow \
  --region us-east-1

# Agent logs
aws logs tail /aws/bedrock-agentcore/runtime/agentcore_qna_agent-LuJi165oYZ \
  --follow \
  --region us-east-1
```

### Metrics

Add custom metrics to track:
- Request count
- Success/failure rate
- Latency
- Memory hit rate

```python
# In your agent code
import time

start = time.time()
result = gateway.invoke_mcp_tool(...)
latency = time.time() - start

logger.info(f"Gateway request completed in {latency:.3f}s")
```

## Security Best Practices

1. **Use IAM Roles**: Instead of access keys, use IAM roles when possible
2. **Least Privilege**: Grant only necessary permissions
3. **Rotate Credentials**: Regularly rotate access keys
4. **Enable Logging**: Enable CloudWatch logging for audit trails
5. **Resource Policies**: Use resource policies to restrict access
6. **Encryption**: Ensure data is encrypted in transit and at rest

## Performance Optimization

1. **Connection Pooling**: Reuse gateway instances
```python
# Singleton pattern
_gateway = None
def get_gateway():
    global _gateway
    if _gateway is None:
        _gateway = AgentCoreGateway(...)
    return _gateway
```

2. **Caching**: Cache frequently accessed memories
3. **Batch Operations**: Retrieve multiple memories in one call
4. **Async Operations**: Use async/await for concurrent requests
5. **Timeout Tuning**: Adjust timeouts based on your needs

## Next Steps

1. ✅ Gateway deployed and tested
2. ✅ Resource policies applied
3. ✅ Agent integrated with gateway
4. ⬜ Add monitoring and alerting
5. ⬜ Implement caching layer
6. ⬜ Add integration tests
7. ⬜ Set up CI/CD pipeline
8. ⬜ Document API for team

## Support

For issues or questions:
1. Check CloudWatch logs
2. Review this guide's troubleshooting section
3. Check AWS AgentCore documentation
4. Review the SUGGESTED_IMPROVEMENTS.md file

## References

- [AWS Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- Project README files in Servers/ and Agents/ directories
