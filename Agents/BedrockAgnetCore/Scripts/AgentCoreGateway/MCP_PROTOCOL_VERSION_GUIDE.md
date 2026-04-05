# MCP Protocol Version Guide

## Supported Versions

AgentCore Gateway supports these MCP protocol versions:
- **2025-06-18** (latest)
- **2025-03-26** (previous)

## Your Current Server Configuration

Based on your code in `Servers/agentcore-memory-mcp/memory_mcp_server.py`:

```python
# Line 61
mcp = FastMCP("agentcore_memory_mcp", host=MCP_HOST, stateless_http=True)

# Line 291
mcp.run(transport="streamable-http")
```

✅ **Good news:** Your server is configured correctly!
- Uses `stateless_http=True` (required for AgentCore)
- Uses `transport="streamable-http"` (correct transport)

## How to Check Protocol Version

### Method 1: Run the Checker Script

```bash
cd Scripts/AgentCoreGateway
python check_mcp_protocol_version.py
```

This will:
1. Check your FastMCP version
2. Try to call the `initialize` method
3. Check server response headers
4. Analyze your server code
5. Provide recommendations

### Method 2: Check FastMCP Version

```bash
pip show fastmcp
```

Look for the version number. FastMCP versions map to MCP protocol versions:
- FastMCP 0.5.0+ → MCP protocol 2025-06-18
- FastMCP 0.4.x → MCP protocol 2025-03-26

### Method 3: Check in Python

```python
import mcp
print(mcp.__version__)

from mcp.server.fastmcp import FastMCP
import inspect
sig = inspect.signature(FastMCP.__init__)
print(list(sig.parameters.keys()))
```

If you see `protocol_version` in the parameters, you can specify it explicitly.

### Method 4: Test with Initialize Call

```python
from Scripts.AgentCoreGateway.mcp_node_caller import AgentCoreCaller

# Make an initialize call
import requests
import json

payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {
            "name": "test-client",
            "version": "1.0.0"
        }
    }
}

# Send to your server and check response
```

## How to Update Protocol Version

### Option 1: Update FastMCP (Recommended)

```bash
pip install --upgrade fastmcp
```

This will get you the latest version with the newest protocol support.

### Option 2: Specify Version Explicitly

If FastMCP supports the `protocol_version` parameter, update your server:

```python
# In Servers/agentcore-memory-mcp/memory_mcp_server.py
# Line 61, change from:
mcp = FastMCP("agentcore_memory_mcp", host=MCP_HOST, stateless_http=True)

# To:
mcp = FastMCP(
    "agentcore_memory_mcp",
    host=MCP_HOST,
    stateless_http=True,
    protocol_version="2025-06-18"  # Specify version explicitly
)
```

### Option 3: Check FastMCP Documentation

```bash
# View FastMCP help
python -c "from mcp.server.fastmcp import FastMCP; help(FastMCP.__init__)"
```

## What If Version Doesn't Match?

### If Your Server Uses Older Version

**Impact:**
- May still work (backward compatibility)
- Some features might not be available
- Gateway might show warnings

**Solution:**
1. Update FastMCP: `pip install --upgrade fastmcp`
2. Redeploy your server: `bedrock-agentcore deploy`
3. Test: `python check_mcp_protocol_version.py`

### If Gateway Requires Specific Version

**Check Gateway Requirements:**
```bash
# Look at gateway error messages
# They will specify required version
```

**Update Server:**
```python
# Specify the required version
mcp = FastMCP(
    "agentcore_memory_mcp",
    host=MCP_HOST,
    stateless_http=True,
    protocol_version="2025-06-18"  # Use required version
)
```

## Compatibility Matrix

| FastMCP Version | MCP Protocol | AgentCore Gateway | Status |
|----------------|--------------|-------------------|---------|
| 0.5.0+ | 2025-06-18 | ✅ Supported | Latest |
| 0.4.x | 2025-03-26 | ✅ Supported | Previous |
| 0.3.x | Earlier | ⚠️ May work | Legacy |

## Testing Protocol Version

### Test 1: Initialize Method

```bash
cd Scripts/AgentCoreGateway
python check_mcp_protocol_version.py
```

Look for output like:
```
Protocol Version: 2025-06-18
✓ Server supports MCP protocol version: 2025-06-18
```

### Test 2: Tools List

```bash
cd Scripts/AgentCoreGateway
python test_gateway.py
```

If tools list works, protocol is compatible.

### Test 3: Server Info

```python
from mcp_node_caller import AgentCoreCaller

caller = AgentCoreCaller(MCP_SERVER_ARN, region)
result = caller.invoke_agent(
    prompt="test",
    actor_id="test",
    session_id="test"
)
# If this works, protocol is compatible
```

## Common Issues

### Issue 1: "Unsupported protocol version"

**Error:**
```
Error: Protocol version X.X.X not supported
```

**Solution:**
```bash
# Update FastMCP
pip install --upgrade fastmcp

# Or specify supported version
protocol_version="2025-06-18"
```

### Issue 2: "Protocol version mismatch"

**Error:**
```
Client requested 2025-06-18 but server uses 2025-03-26
```

**Solution:**
Either:
1. Update server to newer version
2. Or configure gateway to use older version

### Issue 3: No protocol version in response

**Symptom:**
```
Protocol Version: None
```

**Solution:**
Your FastMCP version might not expose protocol version. Update:
```bash
pip install --upgrade fastmcp
```

## Best Practices

### 1. Always Use Latest FastMCP

```bash
pip install --upgrade fastmcp
```

### 2. Pin Version in Requirements

```txt
# In pyproject.toml or requirements.txt
fastmcp>=0.5.0
```

### 3. Test After Updates

```bash
# After updating FastMCP
python check_mcp_protocol_version.py
python test_gateway.py
```

### 4. Document Your Version

```python
# In your server code
# MCP Protocol Version: 2025-06-18
# FastMCP Version: 0.5.0
mcp = FastMCP(...)
```

## Quick Reference

### Check Version
```bash
python check_mcp_protocol_version.py
```

### Update FastMCP
```bash
pip install --upgrade fastmcp
```

### Specify Version
```python
mcp = FastMCP(
    "server_name",
    host="0.0.0.0",
    stateless_http=True,
    protocol_version="2025-06-18"
)
```

### Test Compatibility
```bash
python test_gateway.py
```

## Your Current Status

Based on your server code:

✅ **Correctly configured:**
- Uses `stateless_http=True`
- Uses `transport="streamable-http"`
- Proper FastMCP initialization

⚠️ **To verify:**
- Run `python check_mcp_protocol_version.py`
- Check FastMCP version: `pip show fastmcp`
- Test gateway connection: `python test_gateway.py`

🔧 **If needed:**
- Update FastMCP: `pip install --upgrade fastmcp`
- Redeploy: `bedrock-agentcore deploy`

## Next Steps

1. **Check current version:**
   ```bash
   cd Scripts/AgentCoreGateway
   python check_mcp_protocol_version.py
   ```

2. **If version is old, update:**
   ```bash
   cd Servers/agentcore-memory-mcp
   pip install --upgrade fastmcp
   ```

3. **Redeploy if updated:**
   ```bash
   bedrock-agentcore deploy
   ```

4. **Test:**
   ```bash
   cd ../../Scripts/AgentCoreGateway
   python test_gateway.py
   ```

## Support

- Check version: `check_mcp_protocol_version.py`
- FastMCP docs: https://github.com/jlowin/fastmcp
- MCP protocol: https://modelcontextprotocol.io/
- Your server: `Servers/agentcore-memory-mcp/memory_mcp_server.py`
