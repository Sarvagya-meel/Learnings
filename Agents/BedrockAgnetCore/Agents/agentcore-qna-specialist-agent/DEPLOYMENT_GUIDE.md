# Deployment Guide: QNA Specialist Agent with MCP Memory

This guide walks you through deploying the QNA Specialist Agent with MCP Memory Server integration.

## Prerequisites Checklist

- [ ] Python 3.13+ installed
- [ ] AWS CLI configured with credentials
- [ ] AgentCore CLI installed (`pip install bedrock-agentcore-starter-toolkit`)
- [ ] Groq API key obtained
- [ ] MCP Memory Server deployed (see Step 1)

## Step-by-Step Deployment

### Step 1: Deploy MCP Memory Server

First, deploy the MCP memory server if you haven't already:

```bash
# Navigate to MCP server directory
cd Servers/agentcore-memory-mcp

# Create virtual environment
python3.13 -m venv .venv
source .venv/bin/activate

# Install dependencies
uv sync

# Configure for MCP protocol
agentcore configure -e memory_mcp_server.py --protocol MCP

# Deploy to AWS
agentcore deploy

# Launch the server
agentcore launch
```

**Important**: After deployment, note the endpoint ARN. You'll need to convert it to an HTTP URL.

Example ARN:
```
arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD/runtime-endpoint/DEFAULT
```

Convert to URL format (check AWS console for exact URL):
```
https://agentcore-memory-mcp-server-r4jmv6erzd.us-east-1.amazonaws.com
```

### Step 2: Set Up QNA Specialist Agent

```bash
# Navigate to QNA specialist directory
cd Agents/agentcore-qna-specialist-agent

# Create virtual environment
python3.13 -m venv .venv
source .venv/bin/activate

# Install dependencies
uv sync
```

### Step 3: Configure Environment Variables

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```env
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
MCP_MEMORY_SERVER_URL=https://your-mcp-server-endpoint.amazonaws.com
DEFAULT_ACTOR_ID=qna-specialist-user
DEFAULT_SESSION_ID=default-session
LOG_LEVEL=INFO
```

### Step 4: Test Locally (Optional but Recommended)

Before deploying, test the agent locally:

```bash
python test_mcp_integration.py
```

This will run several tests:
1. Single query without memory
2. Multi-turn conversation with memory
3. Different sessions with separate contexts
4. Error handling

Expected output:
```
✓ Single query test passed
✓ Multi-turn conversation test passed
✓ Session isolation test passed
✓ Error handling test passed
```

### Step 5: Configure AgentCore

```bash
agentcore configure -e 03_agentcore_mcp_memory.py
```

This generates `.bedrock_agentcore.yaml` with the agent configuration.

Review the generated file to ensure:
- Runtime is set to `python3.13`
- Entrypoint points to `03_agentcore_mcp_memory.py`
- Memory mode is configured (if needed)

### Step 6: Deploy the Agent

```bash
agentcore deploy
```

This will:
1. Package your code and dependencies
2. Upload to AWS
3. Create the AgentCore runtime

Expected output:
```
✓ Code packaged successfully
✓ Uploaded to S3
✓ AgentCore runtime created
Agent ARN: arn:aws:bedrock-agentcore:us-east-1:ACCOUNT:runtime/agentcore_qna_specialist-XXXXX
```

### Step 7: Launch the Agent

```bash
agentcore launch \
  --env GROQ_API_KEY=your_groq_key \
  --env MCP_MEMORY_SERVER_URL=your_mcp_url
```

Or use environment variables from `.env`:

```bash
source .env
agentcore launch \
  --env GROQ_API_KEY=$GROQ_API_KEY \
  --env MCP_MEMORY_SERVER_URL=$MCP_MEMORY_SERVER_URL
```

### Step 8: Test the Deployed Agent

```bash
# Test with a simple query
agentcore invoke '{
  "prompt": "What is roaming activation?",
  "actor_id": "user123",
  "session_id": "session456"
}'
```

Expected response:
```json
{
  "result": "Roaming activation allows you to...",
  "actor_id": "user123",
  "session_id": "session456",
  "memory_used": false,
  "memory_stored": true
}
```

### Step 9: Test Multi-Turn Conversation

```bash
# First query
agentcore invoke '{
  "prompt": "What are the roaming charges?",
  "actor_id": "user123",
  "session_id": "session456"
}'

# Second query (should use memory context)
agentcore invoke '{
  "prompt": "How do I activate it?",
  "actor_id": "user123",
  "session_id": "session456"
}'
```

The second response should reference the previous conversation about roaming charges.

## Verification Checklist

After deployment, verify:

- [ ] Agent responds to queries
- [ ] Memory is being stored (`memory_stored: true`)
- [ ] Memory is being retrieved in subsequent queries (`memory_used: true`)
- [ ] Different sessions maintain separate contexts
- [ ] Logs are visible in CloudWatch
- [ ] No errors in agent logs
- [ ] No errors in MCP server logs

## Monitoring

### View Agent Logs

```bash
agentcore logs --follow
```

### View MCP Server Logs

```bash
cd Servers/agentcore-memory-mcp
agentcore logs --follow
```

### Check Agent Status

```bash
agentcore list
```

### Check Memory Storage

You can verify memories are being stored by checking the MCP server logs or using the AWS console to inspect the AgentCore Memory store.

## Troubleshooting

### Issue: Agent deployment fails

**Error**: `Failed to package dependencies`

**Solution**:
```bash
# Ensure you're in the correct directory
cd Agents/agentcore-qna-specialist-agent

# Reinstall dependencies
rm -rf .venv
python3.13 -m venv .venv
source .venv/bin/activate
uv sync
```

### Issue: Memory operations fail

**Error**: `Memory retrieval failed` or `memory_stored: false`

**Solution**:
1. Verify MCP server is running:
   ```bash
   agentcore list
   ```

2. Check MCP server URL is correct in `.env`

3. Test MCP server directly:
   ```bash
   curl -X POST https://your-mcp-server-url/tools/server_info \
     -H "Content-Type: application/json" \
     -d '{"session_id": "test"}'
   ```

### Issue: Agent can't find FAQ data

**Error**: `FileNotFoundError: lauki_qna.csv`

**Solution**:
```bash
# Ensure CSV file is in the agent directory
ls -la lauki_qna.csv

# If missing, copy from another location or create it
```

### Issue: Groq API errors

**Error**: `401 Unauthorized` or `API key invalid`

**Solution**:
1. Verify API key is correct in `.env`
2. Check API key hasn't expired
3. Verify you have credits in your Groq account

### Issue: Different sessions not isolated

**Symptom**: Session A sees memories from Session B

**Solution**:
1. Verify you're using different `session_id` values
2. Check MCP server logs for session handling
3. Ensure `actor_id` is also different if needed

## Updating the Agent

To update the agent after making code changes:

```bash
# 1. Make your changes to 03_agentcore_mcp_memory.py

# 2. Test locally
python test_mcp_integration.py

# 3. Redeploy
agentcore deploy

# 4. Relaunch
agentcore launch \
  --env GROQ_API_KEY=$GROQ_API_KEY \
  --env MCP_MEMORY_SERVER_URL=$MCP_MEMORY_SERVER_URL
```

## Cleanup

To remove the deployed agent:

```bash
# Stop the agent
agentcore stop

# Delete the agent
agentcore delete
```

To remove the MCP server:

```bash
cd Servers/agentcore-memory-mcp
agentcore stop
agentcore delete
```

## Next Steps

After successful deployment:

1. **Deploy Supervisor Agent**: Use the supervisor agent to orchestrate multiple specialists
2. **Add More Specialists**: Create additional specialist agents for different domains
3. **Customize Memory Strategies**: Modify the MCP server to implement custom memory strategies
4. **Add Authentication**: Implement authentication and authorization
5. **Monitor Performance**: Set up CloudWatch dashboards and alarms

## Support Resources

- [AgentCore Documentation](https://docs.aws.amazon.com/bedrock-agentcore/)
- [MCP Server README](../../Servers/agentcore-memory-mcp/README.md)
- [Groq API Documentation](https://console.groq.com/docs)
- [LangChain Documentation](https://python.langchain.com/)

## Common Commands Reference

```bash
# List all agents
agentcore list

# View logs
agentcore logs --follow

# Invoke agent
agentcore invoke '{"prompt": "your question"}'

# Stop agent
agentcore stop

# Delete agent
agentcore delete

# Check agent status
agentcore status
```

---

**Last Updated**: 2026-02-17  
**Version**: 1.0
