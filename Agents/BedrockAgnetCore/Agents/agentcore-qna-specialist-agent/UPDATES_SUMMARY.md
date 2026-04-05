# QNA Specialist Agent - MCP Memory Integration Updates

## Summary

I've updated your QNA Specialist Agent to integrate with your deployed MCP Memory Server. The agent now maintains conversation context across sessions and provides personalized responses based on previous interactions.

## What Was Created

### 1. Main Agent File: `03_agentcore_mcp_memory.py`

**Purpose**: QNA Specialist Agent with full MCP memory integration

**Key Features**:
- Retrieves conversation context from MCP Memory Server before processing queries
- Searches FAQ knowledge base using existing tools
- Generates responses with memory context
- Stores interactions back to MCP Memory Server
- Supports multi-user, multi-session scenarios

**Key Components**:
- `MCPMemoryClient`: HTTP client for MCP server communication
- `retrieve_memory()`: Fetches relevant memories
- `store_interaction()`: Saves conversations
- `process_query_with_memory()`: Main workflow orchestrator
- `agent_invocation()`: AgentCore entrypoint

### 2. Environment Configuration: `.env.example`

**Purpose**: Template for environment variables

**Variables**:
- `GROQ_API_KEY`: Required for LLM
- `MCP_MEMORY_SERVER_URL`: Required for memory operations
- `DEFAULT_ACTOR_ID`: Optional default user identifier
- `DEFAULT_SESSION_ID`: Optional default session identifier
- `LOG_LEVEL`: Optional logging configuration

### 3. Integration Guide: `README_MCP_INTEGRATION.md`

**Purpose**: Comprehensive documentation for MCP integration

**Sections**:
- Architecture overview
- Setup instructions
- Usage examples
- API reference
- Configuration options
- Troubleshooting guide
- Best practices

### 4. Test Script: `test_mcp_integration.py`

**Purpose**: Local testing before deployment

**Test Cases**:
1. Single query without memory context
2. Multi-turn conversation with memory
3. Different sessions with separate contexts
4. Error handling with invalid inputs

**Usage**:
```bash
python test_mcp_integration.py
```

### 5. Deployment Guide: `DEPLOYMENT_GUIDE.md`

**Purpose**: Step-by-step deployment instructions

**Covers**:
- Prerequisites checklist
- MCP server deployment
- Agent setup and configuration
- Local testing
- AWS deployment
- Verification steps
- Troubleshooting
- Monitoring

## How It Works

### Workflow

```
1. User sends query with actor_id and session_id
   ↓
2. Agent retrieves relevant memories from MCP server
   ↓
3. Agent combines memory context with current query
   ↓
4. Agent searches FAQ knowledge base
   ↓
5. Agent generates response using LLM
   ↓
6. Agent stores interaction in MCP server
   ↓
7. Response returned to user
```

### Memory Integration

**Before Processing**:
```python
# Retrieve memories
memories = await mcp_client.retrieve_memory(
    query=query,
    actor_id=actor_id,
    session_id=session_id,
    max_results=5
)

# Format context
memory_context = format_memory_context(memories)

# Combine with query
full_prompt = f"{memory_context}\n\nCurrent question: {query}"
```

**After Processing**:
```python
# Store interaction
await mcp_client.store_interaction(
    user_msg=query,
    assistant_msg=answer,
    actor_id=actor_id,
    session_id=session_id
)
```

## Key Differences from Previous Versions

### `01_agentcore_runtime.py` (Original)
- No memory integration
- Stateless responses
- No conversation context

### `02_agentcore_memory.py` (AgentCore Memory)
- Uses AgentCore's built-in memory
- Requires AgentCore Memory configuration
- Tightly coupled to AgentCore

### `03_agentcore_mcp_memory.py` (New - MCP Integration)
- Uses your deployed MCP Memory Server
- Decoupled architecture
- HTTP-based communication
- Supports external memory access
- Better for multi-agent orchestration

## Configuration Required

### 1. MCP Server Endpoint

You need to get the endpoint URL from your deployed MCP server:

```bash
cd Servers/agentcore-memory-mcp
agentcore list
```

Look for the endpoint ARN and convert to HTTP URL.

### 2. Environment Variables

Create `.env` file:

```env
GROQ_API_KEY=your_actual_key
MCP_MEMORY_SERVER_URL=https://your-mcp-endpoint.amazonaws.com
```

### 3. AgentCore Configuration

The agent will auto-generate `.bedrock_agentcore.yaml` when you run:

```bash
agentcore configure -e 03_agentcore_mcp_memory.py
```

## Testing Before Deployment

**Recommended**: Test locally first

```bash
# 1. Set up environment
cp .env.example .env
# Edit .env with your values

# 2. Install dependencies
python3.13 -m venv .venv
source .venv/bin/activate
uv sync

# 3. Run tests
python test_mcp_integration.py
```

Expected output:
```
✓ TEST 1: Single Query - PASSED
✓ TEST 2: Multi-Turn Conversation - PASSED
✓ TEST 3: Different Sessions - PASSED
✓ TEST 4: Error Handling - PASSED
```

## Deployment Steps (Quick Reference)

```bash
# 1. Navigate to agent directory
cd Agents/agentcore-qna-specialist-agent

# 2. Set up environment
source .venv/bin/activate

# 3. Configure
agentcore configure -e 03_agentcore_mcp_memory.py

# 4. Deploy
agentcore deploy

# 5. Launch
agentcore launch \
  --env GROQ_API_KEY=$GROQ_API_KEY \
  --env MCP_MEMORY_SERVER_URL=$MCP_MEMORY_SERVER_URL

# 6. Test
agentcore invoke '{
  "prompt": "What is roaming activation?",
  "actor_id": "user123",
  "session_id": "session456"
}'
```

## Example Usage

### Single Query

```bash
agentcore invoke '{
  "prompt": "What are the roaming charges?",
  "actor_id": "user123",
  "session_id": "session456"
}'
```

Response:
```json
{
  "result": "Roaming charges vary by country...",
  "actor_id": "user123",
  "session_id": "session456",
  "memory_used": false,
  "memory_stored": true
}
```

### Follow-up Query (with memory)

```bash
agentcore invoke '{
  "prompt": "How do I activate it?",
  "actor_id": "user123",
  "session_id": "session456"
}'
```

Response:
```json
{
  "result": "To activate roaming (which we discussed earlier)...",
  "actor_id": "user123",
  "session_id": "session456",
  "memory_used": true,
  "memory_stored": true
}
```

Notice:
- `memory_used: true` - Agent retrieved previous conversation
- Response references "which we discussed earlier"

## Monitoring

### View Logs

```bash
# Agent logs
agentcore logs --follow

# Look for:
# - "Retrieving memory for actor=..."
# - "Retrieved X memories"
# - "Storing interaction for actor=..."
# - "Interaction stored successfully"
```

### Check Memory Operations

In the response JSON:
- `memory_used: true` - Memories were retrieved and used
- `memory_stored: true` - Interaction was saved

## Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| Memory retrieval fails | Check MCP server URL and deployment status |
| Memory not stored | Verify MCP server is running and accessible |
| No memory context | Ensure previous interactions were stored |
| Agent deployment fails | Check Python version (3.13+) and dependencies |
| Groq API errors | Verify API key and account credits |

## Next Steps

1. **Test the agent**: Run `test_mcp_integration.py`
2. **Deploy**: Follow `DEPLOYMENT_GUIDE.md`
3. **Verify**: Test with multi-turn conversations
4. **Monitor**: Check logs and memory operations
5. **Integrate**: Connect with supervisor agent for orchestration

## Files Reference

```
Agents/agentcore-qna-specialist-agent/
├── 03_agentcore_mcp_memory.py      # Main agent with MCP integration
├── .env.example                     # Environment variables template
├── README_MCP_INTEGRATION.md        # Integration documentation
├── DEPLOYMENT_GUIDE.md              # Deployment instructions
├── test_mcp_integration.py          # Local testing script
└── UPDATES_SUMMARY.md               # This file
```

## Support

For questions or issues:

1. Check `README_MCP_INTEGRATION.md` for detailed documentation
2. Review `DEPLOYMENT_GUIDE.md` for deployment steps
3. Run `test_mcp_integration.py` to diagnose issues
4. Check MCP server logs: `cd Servers/agentcore-memory-mcp && agentcore logs`
5. Review AgentCore documentation: https://docs.aws.amazon.com/bedrock-agentcore/

---

**Created**: 2026-02-17  
**Version**: 1.0  
**Status**: Ready for deployment
