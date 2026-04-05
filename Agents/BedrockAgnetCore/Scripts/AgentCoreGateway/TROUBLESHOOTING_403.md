# Troubleshooting 403 Forbidden Error

## Why You're Getting 403

The gateway is trying to invoke your MCP server, but AWS is rejecting the request because:

1. **Missing Resource Policy**: The MCP server runtime doesn't have a policy allowing invocation
2. **IAM Permissions**: Your credentials might not have permission to invoke the runtime
3. **Service Principal**: The bedrock-agentcore service needs explicit permission

## Quick Diagnosis

Your agent (`03_agentcore_mcp_memory.py`) works fine, which tells us:
- ✅ The MCP server is running
- ✅ Your credentials work for direct invocation
- ❌ The gateway needs additional permissions

## Solution 1: Use Agent's Working Approach (Immediate)

Since your agent already works, you can skip the gateway for now and just improve your existing code:

### Add These 3 Improvements to Your Agent (30 minutes):

1. **Retry Logic** - Add to `MCPMemoryClient._jsonrpc_call`:

```python
import time

def _jsonrpc_call(self, method: str, params: Dict[str, Any], timeout: float = 30.0) -> Any:
    """Make a JSON-RPC call with retry logic"""
    max_attempts = 3
    delay = 1.0
    
    for attempt in range(max_attempts):
        try:
            # Your existing code here
            payload = {...}
            body = json.dumps(payload).encode("utf-8")
            # ... rest of your code
            
            response = requests.post(
                self.invoke_url,
                headers=dict(request.headers),
                data=body,
                timeout=timeout
            )
            response.raise_for_status()
            
            # Parse and return
            return resp_json.get("result", {})
            
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2.0
```

2. **Graceful Degradation** - Modify `process_query_with_memory`:

```python
async def process_query_with_memory(query, actor_id, session_id):
    # Try to get memory, but don't fail if it doesn't work
    memories = []
    try:
        memories = await mcp_client.retrieve_memory(...)
    except Exception as e:
        logger.error(f"Memory failed: {e}")
        # Continue without memory
    
    # Build prompt (works with or without memory)
    memory_context = format_memory_context(memories)
    full_prompt = f"{memory_context}\n\n{query}" if memory_context else query
    
    # Invoke agent (always works)
    result = agent.invoke({"messages": [("human", full_prompt)]})
    answer = result.get("messages", [])[-1].content
    
    # Try to store (best effort)
    try:
        await mcp_client.store_interaction(...)
    except Exception as e:
        logger.error(f"Storage failed: {e}")
    
    return {"result": answer, ...}
```

3. **Relevance Filtering** - Update `format_memory_context`:

```python
def format_memory_context(memories, min_relevance=0.5):
    if not memories:
        return ""
    
    # Filter by relevance
    relevant = [m for m in memories if m.get("relevance", 0) >= min_relevance]
    
    if not relevant:
        return ""
    
    lines = ["Previous context:"]
    for mem in relevant:
        content = mem.get("content", "")
        relevance = mem.get("relevance", 0)
        lines.append(f"- {content} (relevance: {relevance:.2f})")
    
    return "\n".join(lines)
```

**This approach works immediately without fixing the 403 error!**

## Solution 2: Fix Gateway Permissions (For Future)

When you're ready to use the gateway, you'll need to apply the resource policy.

### Check Current Permissions

```bash
aws bedrock-agentcore get-runtime \
  --runtime-arn arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD \
  --region us-east-1
```

### Check Your IAM Permissions

```bash
aws iam get-user
aws iam list-attached-user-policies --user-name YOUR_USERNAME
```

You need these permissions:
- `bedrock-agentcore:InvokeRuntime`
- `bedrock-agentcore:InvokeAgentRuntime`
- `bedrock-agentcore:GetRuntime`

### Apply Resource Policy

The policy file is already created at:
`Servers/agentcore-memory-mcp/mcp_gateway_resource_policy.json`

You need to apply it through:
1. AWS Console (Bedrock → AgentCore → Runtimes → Your Runtime → Permissions)
2. AWS CLI (if the API is available)
3. Contact AWS support if neither works

## Solution 3: Use Agent Credentials in Gateway

Your agent works, so use its credentials:

```bash
# In Scripts/AgentCoreGateway/.env
# Copy the exact credentials from your agent's .env file
AWS_ACCESS_KEY_ID=<same as agent>
AWS_SECRET_ACCESS_KEY=<same as agent>
```

Then test again:

```bash
cd Scripts/AgentCoreGateway
python test_gateway.py
```

## Recommended Path Forward

### Today (5 minutes)
1. ✅ Accept that gateway needs policy setup
2. ✅ Continue using your working agent code
3. ✅ Read `FINAL_RECOMMENDATIONS.md`

### This Week (30 minutes)
4. ✅ Add the 3 improvements to your agent (retry, degradation, filtering)
5. ✅ Test thoroughly
6. ✅ Deploy and monitor

### Later (When Needed)
7. ⬜ Work with AWS to apply resource policy
8. ⬜ Switch to gateway when you add more MCP servers
9. ⬜ Enjoy centralized management

## Why Your Agent Works But Gateway Doesn't

Your agent code uses the same authentication approach, but there might be subtle differences:

1. **Request Format**: Your agent might format requests slightly differently
2. **Headers**: Different headers might be included
3. **Endpoint**: Your agent might use a different endpoint URL
4. **Credentials**: Your agent might use different credentials (IAM role vs access keys)

## Testing Without Gateway

You can test your agent directly:

```bash
cd Agents/agentcore-qna-specialist-agent
python test_mcp_integration.py
```

This should work since your agent already works!

## Summary

**Don't let the 403 error block you!**

Your agent works fine. The gateway is a nice-to-have for when you scale to multiple MCP servers. For now:

1. Use your existing agent code ✅
2. Add the 3 improvements (30 min) ✅
3. Come back to gateway later ⏰

The gateway will be here when you need it, and by then AWS might have better documentation on applying resource policies.
