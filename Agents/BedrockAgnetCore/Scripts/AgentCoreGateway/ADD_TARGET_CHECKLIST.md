# Quick Checklist: Add MCP Server to Gateway

## Pre-Flight Checks

- [ ] MCP server deployed and running
- [ ] AWS credentials configured
- [ ] Access to AgentCore Gateway

## Step-by-Step Checklist

### ☐ Step 1: Verify Server (2 minutes)

```bash
aws bedrock-agentcore get-runtime \
  --runtime-arn arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD \
  --region us-east-1
```

✅ Status should be "ACTIVE"

### ☐ Step 2: Apply Resource Policy (5 minutes)

```bash
cd Servers/agentcore-memory-mcp
python apply_gateway_policy.py
```

If automatic fails, apply manually via AWS Console:
- Bedrock → AgentCore → Runtimes → Your Runtime → Permissions
- Paste policy from script output

### ☐ Step 3: Get Configuration Values (1 minute)

Copy these values:

**Endpoint URL:**
```
https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD/runtime-endpoint/DEFAULT/invocations
```

**Other values:**
- Target Name: `memory-mcp-server`
- Target Type: `MCP_SERVER`
- Protocol: `MCP`
- Protocol Version: `2025-06-18`
- Auth: `AWS_SIGV4`
- Service: `bedrock-agentcore`
- Region: `us-east-1`

### ☐ Step 4: Add Target to Gateway (3 minutes)

**Via AWS Console:**
1. Go to: Bedrock → AgentCore → Gateways → Your Gateway
2. Click "Targets" → "Add Target"
3. Fill in values from Step 3
4. Click "Create"

**Via CLI:**
```bash
aws bedrock-agentcore create-gateway-target \
  --gateway-id YOUR_GATEWAY_ID \
  --target-name memory-mcp-server \
  --target-type MCP_SERVER \
  --endpoint url=https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD/runtime-endpoint/DEFAULT/invocations,protocol=MCP,protocolVersion=2025-06-18 \
  --authentication type=AWS_SIGV4,service=bedrock-agentcore,region=us-east-1 \
  --resource-arn arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD \
  --region us-east-1
```

### ☐ Step 5: Verify Target Added (1 minute)

```bash
aws bedrock-agentcore list-gateway-targets \
  --gateway-id YOUR_GATEWAY_ID \
  --region us-east-1
```

✅ Look for `memory-mcp-server` with status "ACTIVE"

### ☐ Step 6: Test Connection (2 minutes)

```bash
cd Scripts/AgentCoreGateway
python test_gateway.py
```

✅ Should see:
- ✓ Found 3 tools
- ✓ Server info retrieved
- ✓ Tests passing

## Total Time: ~15 minutes

## If Something Fails

### 403 Forbidden?
→ Go back to Step 2, apply resource policy

### 404 Not Found?
→ Check server ARN and endpoint URL

### Connection Timeout?
→ Verify server is running (Step 1)

### Protocol Mismatch?
→ Run: `python check_mcp_protocol_version.py`

## Quick Test Commands

```bash
# Check server status
aws bedrock-agentcore get-runtime --runtime-arn arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD --region us-east-1

# Test gateway connection
cd Scripts/AgentCoreGateway && python test_gateway.py

# Check protocol version
python check_mcp_protocol_version.py
```

## Success Criteria

✅ All these should work:

- [ ] Server status is ACTIVE
- [ ] Resource policy applied
- [ ] Target shows in gateway
- [ ] Tools are discoverable
- [ ] Tools can be invoked
- [ ] Test script passes

## Files You Need

- `mcp_endpoint_config.json` - Configuration
- `ADD_MCP_TARGET_STEPS.md` - Detailed guide
- `test_gateway.py` - Test script
- `apply_gateway_policy.py` - Policy script

## Done! 🎉

Your MCP memory server is now a gateway target.

Agents can now use it to:
- Store conversations
- Retrieve memories
- Check server health

## Next: Use in Your Agent

```python
from agentcore_gateway import AgentCoreGateway

gateway = AgentCoreGateway(region='us-east-1')
gateway.register_server('memory', 'arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD')

# Use it!
result = gateway.invoke_mcp_tool('memory', 'retrieve_memory', {...})
```
