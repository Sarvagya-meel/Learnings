# MCP Node Caller Guide

## Overview

The MCP Node Caller allows you to invoke AgentCore agents from:
- MCP servers
- Other agents
- Python scripts
- Any service that needs to call an agent

## Use Cases

### 1. MCP Server Calling Agent
Your MCP memory server can call the QNA agent to answer questions:
```
User → MCP Server → QNA Agent → Response
```

### 2. Agent-to-Agent Communication
One agent calls another agent:
```
Supervisor Agent → QNA Agent → Response
```

### 3. External Service Integration
Any service can call your agent:
```
Web App → QNA Agent → Response
```

## Quick Start

### 1. Install Dependencies

```bash
cd Scripts/AgentCoreGateway
pip install boto3 requests python-dotenv
```

### 2. Configure Environment

Add to your `.env`:

```bash
# QNA Agent Configuration
QNA_AGENT_ARN=arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_qna_agent-LuJi165oYZ

# AWS Credentials
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

### 3. Test the Caller

```bash
python mcp_node_caller.py
```

This runs 5 examples showing different usage patterns.

## Usage Examples

### Example 1: Simple Call

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

### Example 2: Detailed Call with Memory

```python
from mcp_node_caller import AgentCoreCaller

caller = AgentCoreCaller(agent_arn, region)

result = caller.invoke_agent(
    prompt="How do I activate my service?",
    actor_id="user-123",
    session_id="session-456",
    enable_memory=True
)

print(f"Answer: {result['result']}")
print(f"Memory Used: {result['memory_used']}")
print(f"Memory Stored: {result['memory_stored']}")
```

### Example 3: From MCP Server

```python
from mcp.server.fastmcp import FastMCP
from mcp_node_caller import AgentCoreCaller

mcp = FastMCP("my_server")
agent_caller = AgentCoreCaller(agent_arn, region)

@mcp.tool()
def ask_qna_agent(query: str, actor_id: str) -> dict:
    """Ask the QNA agent a question"""
    result = agent_caller.invoke_agent(
        prompt=query,
        actor_id=actor_id
    )
    return {
        "answer": result.get("result"),
        "memory_used": result.get("memory_used")
    }
```

### Example 4: MCP Protocol Format

```python
from mcp_node_caller import MCPNodeCaller

mcp_caller = MCPNodeCaller(agent_arn, region)

# Returns MCP-formatted response
result = mcp_caller.call_as_mcp_tool(
    prompt="What are the pricing options?",
    actor_id="user-123",
    session_id="session-456"
)

# Result is in MCP tool format:
# {
#   "content": [{"type": "text", "text": "..."}],
#   "isError": false
# }
```

### Example 5: JSON-RPC Format

```python
from mcp_node_caller import MCPNodeCaller

mcp_caller = MCPNodeCaller(agent_arn, region)

# Returns JSON-RPC formatted response
result = mcp_caller.call_as_jsonrpc(
    prompt="Tell me about troubleshooting",
    actor_id="user-123",
    session_id="session-456"
)

# Result is in JSON-RPC format:
# {
#   "jsonrpc": "2.0",
#   "id": 1,
#   "result": {...}
# }
```

## Integration Patterns

### Pattern 1: MCP Server with Agent Backend

Your MCP server exposes tools that internally call the agent:

```python
# In your MCP server
from mcp_node_caller import AgentCoreCaller

agent_caller = AgentCoreCaller(QNA_AGENT_ARN, AWS_REGION)

@mcp.tool()
def answer_question(query: str, user_id: str) -> str:
    """Answer user questions using QNA agent"""
    return agent_caller.invoke_agent_simple(query)

@mcp.tool()
def answer_with_context(query: str, user_id: str, session_id: str) -> dict:
    """Answer with memory context"""
    return agent_caller.invoke_agent(
        prompt=query,
        actor_id=user_id,
        session_id=session_id,
        enable_memory=True
    )
```

### Pattern 2: Agent Orchestration

One agent coordinates multiple agents:

```python
from mcp_node_caller import AgentCoreCaller

# Initialize callers for different agents
qna_caller = AgentCoreCaller(QNA_AGENT_ARN, region)
specialist_caller = AgentCoreCaller(SPECIALIST_AGENT_ARN, region)

def orchestrate_query(query: str, user_id: str):
    """Route query to appropriate agent"""
    
    # Determine which agent to use
    if "faq" in query.lower() or "how" in query.lower():
        return qna_caller.invoke_agent_simple(query)
    else:
        return specialist_caller.invoke_agent_simple(query)
```

### Pattern 3: Batch Processing

Process multiple queries efficiently:

```python
from mcp_node_caller import AgentCoreCaller

caller = AgentCoreCaller(agent_arn, region)

def process_batch(queries: list[str], user_id: str):
    """Process multiple queries"""
    results = []
    
    for query in queries:
        try:
            answer = caller.invoke_agent_simple(query)
            results.append({"query": query, "answer": answer, "success": True})
        except Exception as e:
            results.append({"query": query, "error": str(e), "success": False})
    
    return results
```

## API Reference

### AgentCoreCaller

#### `__init__(agent_arn, region, aws_access_key_id, aws_secret_access_key)`
Initialize the caller.

#### `invoke_agent(prompt, actor_id, session_id, enable_memory, timeout, **kwargs)`
Invoke agent with full control.

**Parameters:**
- `prompt` (str): The user query
- `actor_id` (str, optional): Actor identifier for memory
- `session_id` (str, optional): Session identifier for memory
- `enable_memory` (bool): Whether to use memory (default: True)
- `timeout` (float): Request timeout in seconds (default: 60.0)
- `**kwargs`: Additional parameters to pass to agent

**Returns:** Dict with agent response

#### `invoke_agent_simple(prompt)`
Simple invocation that returns just the answer text.

**Parameters:**
- `prompt` (str): The user query

**Returns:** str - Answer text

### MCPNodeCaller

#### `__init__(agent_arn, region)`
Initialize MCP-specific caller.

#### `call_as_mcp_tool(prompt, actor_id, session_id)`
Call agent and return MCP-formatted response.

**Returns:** MCP tool response format

#### `call_as_jsonrpc(prompt, actor_id, session_id)`
Call agent and return JSON-RPC formatted response.

**Returns:** JSON-RPC response format

## Response Formats

### Standard Response

```json
{
  "result": "The answer to your question...",
  "actor_id": "user-123",
  "session_id": "session-456",
  "memory_used": true,
  "memory_stored": true,
  "processing_time_seconds": 2.5
}
```

### MCP Tool Response

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"result\": \"The answer...\"}"
    }
  ],
  "isError": false
}
```

### JSON-RPC Response

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "result": "The answer...",
    "actor_id": "user-123"
  }
}
```

## Error Handling

### Timeout Errors

```python
try:
    result = caller.invoke_agent(prompt, timeout=30.0)
except requests.exceptions.Timeout:
    print("Agent took too long to respond")
```

### HTTP Errors

```python
try:
    result = caller.invoke_agent(prompt)
except requests.exceptions.HTTPError as e:
    print(f"HTTP {e.response.status_code}: {e.response.text}")
```

### General Errors

```python
try:
    result = caller.invoke_agent(prompt)
except Exception as e:
    print(f"Error: {e}")
```

## Best Practices

### 1. Reuse Caller Instances

```python
# Good - reuse instance
caller = AgentCoreCaller(agent_arn, region)
for query in queries:
    result = caller.invoke_agent(query)

# Bad - create new instance each time
for query in queries:
    caller = AgentCoreCaller(agent_arn, region)  # Wasteful
    result = caller.invoke_agent(query)
```

### 2. Set Appropriate Timeouts

```python
# Quick queries
result = caller.invoke_agent(prompt, timeout=10.0)

# Complex queries
result = caller.invoke_agent(prompt, timeout=60.0)
```

### 3. Use Memory Consistently

```python
# Use same actor_id and session_id for conversation
actor_id = "user-123"
session_id = "conversation-456"

for query in conversation:
    result = caller.invoke_agent(
        prompt=query,
        actor_id=actor_id,
        session_id=session_id
    )
```

### 4. Handle Errors Gracefully

```python
def safe_invoke(prompt):
    try:
        return caller.invoke_agent_simple(prompt)
    except Exception as e:
        logger.error(f"Agent call failed: {e}")
        return "I'm sorry, I couldn't process that request."
```

## Testing

### Test Basic Connectivity

```bash
python mcp_node_caller.py
```

### Test from Your Code

```python
from mcp_node_caller import AgentCoreCaller

def test_agent_caller():
    caller = AgentCoreCaller(agent_arn, region)
    
    # Test simple call
    answer = caller.invoke_agent_simple("test query")
    assert answer is not None
    
    # Test detailed call
    result = caller.invoke_agent("test query")
    assert "result" in result
    
    print("✓ All tests passed")

test_agent_caller()
```

## Troubleshooting

### 403 Forbidden

**Issue:** Agent returns 403 error

**Solution:** Check IAM permissions. Your credentials need:
- `bedrock-agentcore:InvokeRuntime`
- `bedrock-agentcore:InvokeAgentRuntime`

### Timeout

**Issue:** Requests timeout

**Solution:** 
1. Increase timeout: `caller.invoke_agent(prompt, timeout=120.0)`
2. Check agent is running: `aws bedrock-agentcore list-runtimes`
3. Check agent logs in CloudWatch

### Invalid Response

**Issue:** Can't parse agent response

**Solution:** Check agent is returning proper JSON format

## Complete Example: MCP Server

See `mcp_server_with_agent_caller.py` for a complete example of an MCP server that:
- Exposes tools to call the QNA agent
- Handles errors gracefully
- Supports batch processing
- Includes health checks

## Next Steps

1. Test the caller: `python mcp_node_caller.py`
2. Integrate into your MCP server
3. Test end-to-end
4. Deploy and monitor

## Support

- Check logs: `aws logs tail /aws/bedrock-agentcore/runtime/agentcore_qna_agent-LuJi165oYZ --follow`
- Test connectivity: Run the examples
- Review agent code: `Agents/agentcore-qna-specialist-agent/03_agentcore_mcp_memory.py`
