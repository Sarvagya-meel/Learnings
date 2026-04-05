# QNA Specialist Agent with MCP Memory Integration

This document explains how to set up and use the QNA Specialist Agent with MCP Memory Server integration.

## Overview

The `03_agentcore_mcp_memory.py` file provides a QNA specialist agent that:
- Answers FAQ questions using a knowledge base
- Retrieves conversation context from your deployed MCP Memory Server
- Stores interactions back to the MCP Memory Server
- Supports multi-user, multi-session scenarios with `actor_id` and `session_id`

## Architecture

```
User Query
    ↓
QNA Specialist Agent
    ↓
1. Retrieve Memory (from MCP Server)
    ↓
2. Search FAQ Knowledge Base
    ↓
3. Generate Response (with memory context)
    ↓
4. Store Interaction (to MCP Server)
    ↓
Response to User
```

## Prerequisites

1. **Deployed MCP Memory Server**: You must have the MCP memory server deployed and accessible
   - Location: `Servers/agentcore-memory-mcp/`
   - Get the endpoint URL after deployment

2. **Python 3.13+**: Required for AgentCore runtime

3. **API Keys**:
   - Groq API key for LLM
   - HuggingFace API key (optional, for embeddings)

## Setup Instructions

### Step 1: Deploy MCP Memory Server (if not already done)

```bash
cd Servers/agentcore-memory-mcp
source .venv/bin/activate
agentcore configure -e memory_mcp_server.py --protocol MCP
agentcore deploy
agentcore launch
```

After deployment, note the endpoint URL. It will look like:
```
arn:aws:bedrock-agentcore:us-east-1:ACCOUNT_ID:runtime/agentcore_memory_mcp_server-XXXXX/runtime-endpoint/DEFAULT
```

### Step 2: Configure Environment Variables

Create a `.env` file in the `agentcore-qna-specialist-agent` directory:

```bash
cd Agents/agentcore-qna-specialist-agent
cp .env.example .env
```

Edit `.env` and add your configuration:

```env
GROQ_API_KEY=your_actual_groq_api_key
MCP_MEMORY_SERVER_URL=https://your-mcp-server-endpoint.amazonaws.com
```

### Step 3: Install Dependencies

```bash
# Create virtual environment
python3.13 -m venv .venv
source .venv/bin/activate

# Install dependencies
uv sync
# or
pip install -r requirements.txt
```

### Step 4: Configure AgentCore

```bash
agentcore configure -e 03_agentcore_mcp_memory.py
```

This generates `.bedrock_agentcore.yaml` with the agent configuration.

### Step 5: Deploy the Agent

```bash
agentcore deploy
agentcore launch --env GROQ_API_KEY=your_key --env MCP_MEMORY_SERVER_URL=your_url
```

## Usage

### Basic Invocation

```bash
agentcore invoke '{
  "prompt": "What is roaming activation?",
  "actor_id": "user123",
  "session_id": "session456"
}'
```

### Response Format

```json
{
  "result": "Roaming activation allows you to...",
  "actor_id": "user123",
  "session_id": "session456",
  "memory_used": true,
  "memory_stored": true
}
```

### Multi-Turn Conversation Example

**First Query:**
```bash
agentcore invoke '{
  "prompt": "What are the roaming charges?",
  "actor_id": "user123",
  "session_id": "session456"
}'
```

**Second Query (with context):**
```bash
agentcore invoke '{
  "prompt": "How do I activate it?",
  "actor_id": "user123",
  "session_id": "session456"
}'
```

The agent will retrieve the previous conversation about roaming charges and provide a contextual response about activation.

## How It Works

### 1. Memory Retrieval

Before processing each query, the agent:
- Calls `mcp_client.retrieve_memory()` with the user's query
- Retrieves up to 5 relevant memories from previous conversations
- Formats the memories into a context string

### 2. Query Processing

The agent:
- Combines memory context with the current query
- Uses LangChain tools to search the FAQ knowledge base
- Generates a response using Groq LLM

### 3. Memory Storage

After generating a response, the agent:
- Calls `mcp_client.store_interaction()` with the user query and assistant response
- Stores the interaction in the MCP Memory Server for future retrieval

## MCP Memory Client API

### Retrieve Memory

```python
memories = await mcp_client.retrieve_memory(
    query="user question",
    actor_id="user123",
    session_id="session456",
    max_results=5
)
```

Returns:
```python
[
    {
        "memory_index": 1,
        "strategy": "GeneralStore",
        "content": "Previous conversation content",
        "relevance": 0.85
    },
    ...
]
```

### Store Interaction

```python
success = await mcp_client.store_interaction(
    user_msg="What is roaming?",
    assistant_msg="Roaming allows you to...",
    actor_id="user123",
    session_id="session456"
)
```

Returns: `True` if successful, `False` otherwise

## Configuration Options

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | Yes | - | API key for Groq LLM |
| `MCP_MEMORY_SERVER_URL` | Yes | - | MCP server endpoint URL |
| `DEFAULT_ACTOR_ID` | No | `qna-specialist-user` | Default actor identifier |
| `DEFAULT_SESSION_ID` | No | `default-session` | Default session identifier |
| `LOG_LEVEL` | No | `INFO` | Logging level |

### Agent Configuration

In `03_agentcore_mcp_memory.py`, you can adjust:

```python
# Number of memories to retrieve
max_results=5

# FAQ search results
k=3  # for search_faq
k=5  # for search_detailed_faq

# LLM temperature
temperature=0
```

## Troubleshooting

### Issue: Memory retrieval fails

**Symptoms**: Logs show "Memory retrieval failed"

**Solutions**:
1. Verify MCP server is deployed and running:
   ```bash
   agentcore list
   ```

2. Check the MCP server endpoint URL in `.env`

3. Verify network connectivity between agent and MCP server

4. Check MCP server logs for errors

### Issue: Memory not being stored

**Symptoms**: `memory_stored: false` in response

**Solutions**:
1. Check MCP server logs for storage errors
2. Verify actor_id and session_id are valid strings
3. Ensure user_msg and assistant_msg are non-empty

### Issue: No memory context in responses

**Symptoms**: Agent doesn't reference previous conversations

**Solutions**:
1. Verify memories are being stored (check `memory_stored` in response)
2. Check if query is semantically similar to previous conversations
3. Increase `max_results` parameter in memory retrieval
4. Check MCP server memory ID configuration

### Issue: Agent deployment fails

**Symptoms**: `agentcore deploy` or `agentcore launch` fails

**Solutions**:
1. Verify Python 3.13+ is installed
2. Check all dependencies are installed
3. Verify AWS credentials are configured
4. Check `.bedrock_agentcore.yaml` is properly generated

## Testing Locally

You can test the agent locally before deployment:

```python
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test():
    payload = {
        "prompt": "What is roaming activation?",
        "actor_id": "test-user",
        "session_id": "test-session"
    }
    
    result = await agent_invocation(payload, {})
    print(result)

asyncio.run(test())
```

## Monitoring

### Logs

The agent logs all operations:
- Memory retrieval attempts and results
- FAQ searches
- Response generation
- Memory storage attempts

View logs in CloudWatch or locally:
```bash
agentcore logs --follow
```

### Key Metrics to Monitor

- Memory retrieval success rate
- Memory storage success rate
- Response latency
- Error rates

## Best Practices

1. **Use meaningful actor_id and session_id**: This helps organize memories and enables proper context retrieval

2. **Handle memory failures gracefully**: The agent continues to work even if memory operations fail

3. **Monitor memory storage**: Ensure interactions are being stored for future context

4. **Test with multiple sessions**: Verify that different sessions maintain separate contexts

5. **Adjust max_results**: Tune the number of memories retrieved based on your use case

## Next Steps

- Deploy the supervisor agent to orchestrate multiple specialist agents
- Add more specialist agents for different domains
- Implement custom memory strategies in the MCP server
- Add authentication and authorization

## Support

For issues or questions:
1. Check the main README.md
2. Review MCP server documentation in `Servers/agentcore-memory-mcp/README.md`
3. Check AgentCore documentation: https://docs.aws.amazon.com/bedrock-agentcore/

---

**Author**: Updated for MCP Memory Integration  
**Date**: 2026-02-17
