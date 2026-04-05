# AgentCore Gateway - Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies (30 seconds)

```bash
cd Scripts/AgentCoreGateway
pip install -r requirements.txt
```

### 2. Configure Environment (1 minute)

Create `.env` file:

```bash
cat > .env << EOF
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
MCP_MEMORY_SERVER_ARN=arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD
EOF
```

### 3. Apply Resource Policy (1 minute)

```bash
cd ../../Servers/agentcore-memory-mcp
python apply_gateway_policy.py
```

If automatic application fails, follow the manual steps shown.

### 4. Test Gateway (2 minutes)

```bash
cd ../../Scripts/AgentCoreGateway
python test_gateway.py
```

Expected: All tests pass ✓

### 5. Use in Your Agent (1 minute)

```python
from Scripts.AgentCoreGateway.agentcore_gateway import AgentCoreGateway

# Initialize
gateway = AgentCoreGateway()
gateway.register_server("memory", MCP_SERVER_ARN)

# Use
result = gateway.invoke_mcp_tool(
    "memory",
    "retrieve_memory",
    {"query": "test", "actor_id": "user", "session_id": "session"}
)
```

## Common Commands

### Test Gateway
```bash
python test_gateway.py
```

### Run Example
```bash
python agentcore_gateway.py
```

### Check Server Health
```bash
python -c "
from agentcore_gateway import AgentCoreGateway
import os
gw = AgentCoreGateway()
gw.register_server('memory', os.getenv('MCP_MEMORY_SERVER_ARN'))
print(gw.get_server_info('memory'))
"
```

### List Available Tools
```bash
python -c "
from agentcore_gateway import AgentCoreGateway
import os
gw = AgentCoreGateway()
gw.register_server('memory', os.getenv('MCP_MEMORY_SERVER_ARN'))
tools = gw.list_tools('memory')
for t in tools:
    print(f\"- {t['name']}: {t.get('description', 'No description')}\")
"
```

## Troubleshooting

### 403 Forbidden
```bash
# Check resource policy
cd ../../Servers/agentcore-memory-mcp
python apply_gateway_policy.py
```

### Connection Timeout
```bash
# Check if server is running
aws bedrock-agentcore list-runtimes --region us-east-1
```

### Import Error
```bash
# Ensure you're in the right directory
cd Scripts/AgentCoreGateway
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## Next Steps

1. ✅ Gateway working? → Read [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. ✅ Want to improve agent? → Read [MCP_SERVER_CHANGES.md](MCP_SERVER_CHANGES.md)
3. ✅ Need more features? → Read [SUGGESTED_IMPROVEMENTS.md](SUGGESTED_IMPROVEMENTS.md)
4. ✅ Ready to deploy? → Read [README.md](README.md)

## Quick Reference

### Gateway Methods

```python
# Initialize
gateway = AgentCoreGateway(region, access_key, secret_key)

# Register server
gateway.register_server(name, arn, description, tags)

# List tools
tools = gateway.list_tools(server_name, timeout)

# Invoke tool
result = gateway.invoke_mcp_tool(server_name, tool_name, arguments, timeout)

# Health check
info = gateway.get_server_info(server_name, session_id)
```

### Memory Tools

```python
# Store interaction
gateway.invoke_mcp_tool("memory", "store_interaction", {
    "user_msg": "question",
    "assistant_msg": "answer",
    "actor_id": "user123",
    "session_id": "session456"
})

# Retrieve memory
gateway.invoke_mcp_tool("memory", "retrieve_memory", {
    "query": "search query",
    "max_results": 5,
    "actor_id": "user123",
    "session_id": "session456"
})

# Server info
gateway.invoke_mcp_tool("memory", "server_info", {
    "session_id": "session456"
})
```

## Support

- Check logs: `aws logs tail /aws/bedrock-agentcore/runtime/...`
- Review docs: See README.md and other guides
- Test connection: Run `test_gateway.py`

## Files Overview

```
Scripts/AgentCoreGateway/
├── agentcore_gateway.py          # Main gateway implementation
├── gateway_config.json            # Configuration file
├── test_gateway.py                # Test suite
├── example_agent_with_gateway.py  # Example integration
├── requirements.txt               # Dependencies
├── README.md                      # Full documentation
├── QUICK_START.md                 # This file
├── DEPLOYMENT_GUIDE.md            # Deployment instructions
├── MCP_SERVER_CHANGES.md          # Agent improvements
└── SUGGESTED_IMPROVEMENTS.md      # Future enhancements
```
