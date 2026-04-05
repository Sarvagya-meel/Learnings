# MCP Endpoint - Quick Reference Card

## Your MCP Server Endpoint

### Copy-Paste Ready Values

**MCP Endpoint URL:**
```
https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD/runtime-endpoint/DEFAULT/invocations
```

**Server ARN:**
```
arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD
```

**Protocol:** `MCP`

**Protocol Version:** `2025-06-18`

**Authentication:** `AWS_SIGV4`

**Service:** `bedrock-agentcore`

**Region:** `us-east-1`

## Available Tools

1. **retrieve_memory** - Get stored memories
2. **store_interaction** - Save conversations
3. **server_info** - Health check

## Configuration Files

- **JSON Config:** `mcp_endpoint_config.json`
- **Full Guide:** `MCP_ENDPOINT_CONFIGURATION.md`
- **Test Script:** `test_gateway.py`

## Quick Test

```bash
cd Scripts/AgentCoreGateway
python test_gateway.py
```

## If You Get 403 Error

Apply resource policy:
```bash
cd ../../Servers/agentcore-memory-mcp
python apply_gateway_policy.py
```

Then follow manual steps in the output.

## Gateway Target Form Fields

When filling out a gateway target configuration form:

| Field | Value |
|-------|-------|
| Target Name | `memory-mcp-server` |
| Target Type | `MCP_SERVER` |
| Endpoint URL | See "MCP Endpoint URL" above |
| Protocol | `MCP` |
| Protocol Version | `2025-06-18` |
| Auth Type | `AWS_SIGV4` |
| Service | `bedrock-agentcore` |
| Region | `us-east-1` |
| Resource ARN | See "Server ARN" above |

## Alternative Endpoint Format

If the first format doesn't work, try this URL-encoded version:

```
https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn%3Aaws%3Abedrock-agentcore%3Aus-east-1%3A662403250828%3Aruntime%2Fagentcore_memory_mcp_server-R4jmV6ERZD/invocations?qualifier=DEFAULT
```

## Server Details

- **Server ID:** agentcore_memory_mcp_server-R4jmV6ERZD
- **Account:** 662403250828
- **Region:** us-east-1
- **Runtime:** Python 3.13
- **Memory ID:** MyAgentMemory20260211160131-gMGdB67nD0

## Need Help?

1. Full configuration: `MCP_ENDPOINT_CONFIGURATION.md`
2. Test connection: `python test_gateway.py`
3. Check version: `python check_mcp_protocol_version.py`
4. Apply policy: See `apply_policy_manual.md`
