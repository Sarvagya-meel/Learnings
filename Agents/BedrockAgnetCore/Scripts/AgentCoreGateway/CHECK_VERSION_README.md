# How to Check MCP Protocol Version

## Quick Check (30 seconds)

```bash
cd Scripts/AgentCoreGateway
python check_mcp_protocol_version.py
```

This will tell you:
- ✅ What protocol version your server uses
- ✅ If it's compatible with AgentCore Gateway (2025-06-18 or 2025-03-26)
- ✅ What FastMCP version you have
- ✅ If you need to update

## What You'll See

### If Compatible ✅
```
Protocol Version: 2025-06-18
✓ Server supports MCP protocol version: 2025-06-18

FastMCP Version: 0.5.0
✓ Compatible with AgentCore Gateway
```

### If Update Needed ⚠️
```
Protocol Version: 2025-01-15
⚠ Server version may not be supported
Supported versions: 2025-06-18, 2025-03-26

Recommendation: Update FastMCP
```

## How to Update (if needed)

### 1. Update FastMCP
```bash
cd Servers/agentcore-memory-mcp
pip install --upgrade fastmcp
```

### 2. Redeploy Server
```bash
bedrock-agentcore deploy
```

### 3. Verify
```bash
cd ../../Scripts/AgentCoreGateway
python check_mcp_protocol_version.py
```

## Your Current Server

Your server (`Servers/agentcore-memory-mcp/memory_mcp_server.py`) is configured correctly:

```python
# Line 61 - Good configuration
mcp = FastMCP("agentcore_memory_mcp", host=MCP_HOST, stateless_http=True)

# Line 291 - Correct transport
mcp.run(transport="streamable-http")
```

✅ Uses `stateless_http=True` (required)
✅ Uses `streamable-http` transport (correct)

Just need to verify the FastMCP version supports the right protocol.

## Supported Versions

AgentCore Gateway supports:
- **2025-06-18** (latest, recommended)
- **2025-03-26** (previous, still supported)

## Quick Commands

```bash
# Check protocol version
python check_mcp_protocol_version.py

# Check FastMCP version
pip show fastmcp

# Update FastMCP
pip install --upgrade fastmcp

# Test gateway connection
python test_gateway.py
```

## What If It Doesn't Work?

1. **Check FastMCP is installed:**
   ```bash
   pip show fastmcp
   ```

2. **Install if missing:**
   ```bash
   pip install fastmcp
   ```

3. **Update to latest:**
   ```bash
   pip install --upgrade fastmcp
   ```

4. **Check server is deployed:**
   ```bash
   aws bedrock-agentcore list-runtimes --region us-east-1
   ```

## More Details

See `MCP_PROTOCOL_VERSION_GUIDE.md` for:
- Detailed version compatibility matrix
- How to specify version explicitly
- Troubleshooting guide
- Best practices

## Summary

1. Run: `python check_mcp_protocol_version.py`
2. If version is 2025-06-18 or 2025-03-26 → ✅ You're good!
3. If older version → Update FastMCP and redeploy
4. Test with: `python test_gateway.py`

That's it! 🚀
