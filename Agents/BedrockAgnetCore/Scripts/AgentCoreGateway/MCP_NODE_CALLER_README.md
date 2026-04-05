# MCP Node Caller - Quick Reference

## What Is This?

The MCP Node Caller allows you to invoke your QNA Agent from:
- MCP servers
- Other agents  
- Python scripts
- Any service

## Quick Start (2 minutes)

### 1. Setup Environment

```bash
cd Scripts/AgentCoreGateway

# Copy and edit .env
cp .env.example .env
# Edit .env with your AWS credentials
```

### 2. Test It

```bash
python test_agent_caller.py
```

Expected output:
```
✓ SUCCESS!
Answer: Bottle gourd (lauki) is...
```

### 3. Use It

```python
from mcp_node_caller import AgentCoreCaller

# Initialize
caller = AgentCoreCaller(
    agent_arn="arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_qna_agent-LuJi165oYZ",
    region="us-east-1"
)

# Ask a question
answer = caller.invoke_agent_simple("What is bottle gourd?")
print(answer)
```

## Files

- **mcp_node_caller.py** - Main implementation
- **test_agent_caller.py** - Quick test script
- **mcp_server_with_agent_caller.py** - Example MCP server integration
- **MCP_NODE_CALLER_GUIDE.md** - Complete documentation

## Common Use Cases

### Use Case 1: MCP Server Calls Agent

```python
# In your MCP server
from mcp.server.fastmcp import FastMCP
from mcp_node_caller import AgentCoreCaller

mcp = FastMCP("my_server")
agent_caller = AgentCoreCaller(agent_arn, region)

@mcp.tool()
def ask_agent(query: str) -> str:
    """Ask the QNA agent"""
    return agent_caller.invoke_agent_simple(query)
```

### Use Case 2: Agent-to-Agent Call

```python
# One agent calling another
from mcp_node_caller import AgentCoreCaller

qna_caller = AgentCoreCaller(QNA_AGENT_ARN, region)

def delegate_to_qna(query: str):
    """Delegate FAQ questions to QNA agent"""
    return qna_caller.invoke_agent_simple(query)
```

### Use Case 3: Batch Processing

```python
from mcp_node_caller import AgentCoreCaller

caller = AgentCoreCaller(agent_arn, region)

queries = ["Question 1?", "Question 2?", "Question 3?"]

for query in queries:
    answer = caller.invoke_agent_simple(query)
    print(f"Q: {query}\nA: {answer}\n")
```

## API Quick Reference

### Simple Call (Just Get Answer)

```python
answer = caller.invoke_agent_simple("Your question here")
```

### Detailed Call (With Memory)

```python
result = caller.invoke_agent(
    prompt="Your question",
    actor_id="user-123",
    session_id="session-456",
    enable_memory=True
)

print(result['result'])  # The answer
print(result['memory_used'])  # True/False
print(result['memory_stored'])  # True/False
```

### MCP Format

```python
from mcp_node_caller import MCPNodeCaller

mcp_caller = MCPNodeCaller(agent_arn, region)

result = mcp_caller.call_as_mcp_tool(
    prompt="Your question",
    actor_id="user-123"
)
# Returns MCP tool format
```

## Troubleshooting

### Test Failed?

1. **Check .env file** - Ensure AWS credentials are correct
2. **Check agent ARN** - Verify it matches your deployed agent
3. **Check IAM permissions** - Need `bedrock-agentcore:InvokeRuntime`
4. **Check agent is running** - `aws bedrock-agentcore list-runtimes`

### 403 Forbidden?

Your IAM user/role needs these permissions:
```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock-agentcore:InvokeRuntime",
    "bedrock-agentcore:InvokeAgentRuntime"
  ],
  "Resource": "*"
}
```

### Timeout?

Increase timeout:
```python
result = caller.invoke_agent(prompt, timeout=120.0)
```

## Examples

Run all examples:
```bash
python mcp_node_caller.py
```

This shows:
1. Simple call
2. Detailed call with memory
3. MCP tool format
4. JSON-RPC format
5. Batch processing

## Integration Example

See `mcp_server_with_agent_caller.py` for a complete MCP server that:
- Exposes tools to call the QNA agent
- Handles errors gracefully
- Supports batch processing
- Includes health checks

## Next Steps

1. ✅ Test: `python test_agent_caller.py`
2. ✅ Read: `MCP_NODE_CALLER_GUIDE.md`
3. ✅ Integrate: Use in your MCP server
4. ✅ Deploy: Test end-to-end

## Support

- Full guide: `MCP_NODE_CALLER_GUIDE.md`
- Example server: `mcp_server_with_agent_caller.py`
- Test script: `test_agent_caller.py`
- Main code: `mcp_node_caller.py`

## Summary

The MCP Node Caller makes it easy to invoke your QNA agent from anywhere. It handles:
- ✅ AWS authentication
- ✅ Request signing
- ✅ Error handling
- ✅ Multiple response formats
- ✅ Memory support

Just initialize and call - it's that simple!
