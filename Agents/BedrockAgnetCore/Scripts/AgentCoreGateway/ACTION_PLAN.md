# Action Plan: What to Do Next

## Current Situation

✅ **What's Working:**
- Your MCP server is deployed and running
- Your agent (`03_agentcore_mcp_memory.py`) successfully invokes the MCP server
- Memory retrieval and storage work
- Your agent responds to queries

❌ **What's Not Working:**
- Gateway gets 403 Forbidden errors
- Resource policy API not available in boto3
- Need manual policy application

## Recommended Path: Focus on What Works

### Option A: Improve Your Agent (RECOMMENDED - 30 minutes)

Since your agent already works, enhance it with these quick wins:

#### Step 1: Add Retry Logic (10 minutes)

Open `Agents/agentcore-qna-specialist-agent/03_agentcore_mcp_memory.py`

Add this function after line 50:

```python
import time

def retry_with_backoff(func, max_attempts=3, initial_delay=1.0):
    """Retry with exponential backoff"""
    delay = initial_delay
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            logger.warning(f"Retry {attempt + 1}/{max_attempts} after {delay}s")
            time.sleep(delay)
            delay *= 2.0
```

Then in `_jsonrpc_call` method (around line 90), wrap the request:

```python
response = retry_with_backoff(
    lambda: requests.post(self.invoke_url, headers=signed_headers, data=body, timeout=timeout)
)
```

#### Step 2: Add Graceful Degradation (10 minutes)

In `process_query_with_memory` (around line 200), wrap memory calls:

```python
# Step 1: Try memory (don't fail if it doesn't work)
memories = []
memory_error = None
try:
    memories = await mcp_client.retrieve_memory(...)
except Exception as e:
    logger.error(f"Memory failed: {e}")
    memory_error = str(e)
    # Continue without memory

# ... rest of code ...

# Step 5: Try to store (best effort)
store_success = False
try:
    store_success = await mcp_client.store_interaction(...)
except Exception as e:
    logger.error(f"Storage failed: {e}")

return {
    "result": answer,
    "memory_error": memory_error,  # Add this
    ...
}
```

#### Step 3: Add Relevance Filtering (5 minutes)

In `format_memory_context` (around line 180):

```python
def format_memory_context(memories, min_relevance=0.5):
    if not memories:
        return ""
    
    # Filter by relevance
    relevant = [m for m in memories if m.get("relevance", 0) >= min_relevance]
    
    if not relevant:
        logger.info(f"No memories above {min_relevance} relevance")
        return ""
    
    lines = ["Previous context:"]
    for mem in relevant:
        content = mem.get("content", "")
        relevance = mem.get("relevance", 0)
        lines.append(f"- {content} (relevance: {relevance:.2f})")
    
    return "\n".join(lines)
```

#### Step 4: Test (5 minutes)

```bash
cd Agents/agentcore-qna-specialist-agent
python test_mcp_integration.py
```

**Total Time: 30 minutes**
**Result: More reliable agent with better error handling**

### Option B: Fix Gateway Permissions (Time Unknown)

This requires working with AWS to apply the resource policy:

1. Contact AWS Support
2. Ask about applying resource policies to AgentCore runtimes
3. Provide the policy from `mcp_gateway_resource_policy.json`
4. Wait for resolution
5. Test gateway again

**Total Time: Unknown (could be days/weeks)**
**Result: Gateway works, but agent already works**

## My Recommendation

**Choose Option A** because:

1. ✅ Works immediately (30 minutes)
2. ✅ Improves your existing working code
3. ✅ No dependencies on AWS support
4. ✅ High-value improvements
5. ✅ Low risk

**Skip Option B for now** because:

1. ❌ Time unknown
2. ❌ Requires AWS support
3. ❌ Gateway is optional (nice-to-have)
4. ❌ Your agent already works
5. ❌ Can do this later when you need multiple MCP servers

## Detailed Steps for Option A

### 1. Backup Your Agent File

```bash
cd Agents/agentcore-qna-specialist-agent
cp 03_agentcore_mcp_memory.py 03_agentcore_mcp_memory.py.backup
```

### 2. Open the File

```bash
# Use your preferred editor
code 03_agentcore_mcp_memory.py
# or
vim 03_agentcore_mcp_memory.py
```

### 3. Make Changes

Follow the code snippets in Step 1, 2, and 3 above.

### 4. Test Locally

```bash
python test_mcp_integration.py
```

### 5. Deploy

```bash
bedrock-agentcore deploy
```

### 6. Monitor

```bash
aws logs tail /aws/bedrock-agentcore/runtime/agentcore_qna_agent-LuJi165oYZ --follow
```

## What About the Gateway?

The gateway is ready to use when you need it. Come back to it when:

1. You add a 2nd MCP server
2. You need centralized management
3. AWS provides better resource policy APIs
4. You have time to work with AWS support

For now, it's documented and ready in `Scripts/AgentCoreGateway/`.

## Success Metrics

After implementing Option A, you should see:

- ✅ Agent handles MCP failures gracefully
- ✅ Retries work on transient errors
- ✅ Only relevant memories used in context
- ✅ No crashes from memory service issues
- ✅ Better logs showing retry attempts

## Timeline

### Today (30 minutes)
- [ ] Backup agent file
- [ ] Add retry logic
- [ ] Add graceful degradation
- [ ] Add relevance filtering
- [ ] Test locally

### Tomorrow (15 minutes)
- [ ] Deploy to dev
- [ ] Monitor logs
- [ ] Test with real queries

### This Week (30 minutes)
- [ ] Deploy to production
- [ ] Monitor metrics
- [ ] Gather feedback
- [ ] Document changes

### Later (When Needed)
- [ ] Work on gateway permissions
- [ ] Add more MCP servers
- [ ] Switch to gateway

## Questions?

- **Q: Should I fix the gateway first?**
  - A: No, improve your working agent first

- **Q: Will I need the gateway eventually?**
  - A: Maybe, if you add more MCP servers

- **Q: Is my current agent code bad?**
  - A: No! It's good. These are enhancements.

- **Q: How long to fix the 403 error?**
  - A: Unknown. Depends on AWS support/documentation.

- **Q: Can I use both approaches?**
  - A: Yes! Improve agent now, add gateway later.

## Next Action

**Right now, do this:**

```bash
cd Agents/agentcore-qna-specialist-agent
cp 03_agentcore_mcp_memory.py 03_agentcore_mcp_memory.py.backup
# Then open the file and add the 3 improvements
```

Start with retry logic - it's the highest value improvement!

## Resources

- `FINAL_RECOMMENDATIONS.md` - Detailed improvement guide
- `TROUBLESHOOTING_403.md` - Understanding the 403 error
- `apply_policy_manual.md` - How to fix gateway (later)
- Your backup file - Rollback if needed

Good luck! Focus on what works. 🚀
