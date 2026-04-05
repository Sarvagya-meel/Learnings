# Testing Instructions for MCP Memory Integration

## What Was Updated

We've implemented JSON-RPC over HTTP with AWS SigV4 authentication to properly communicate with the MCP Memory Server.

### Files Modified:
1. `03_agentcore_mcp_memory.py` - Now uses JSON-RPC with AWS SigV4 authentication
2. `.env` - Updated to use `MCP_MEMORY_SERVER_ARN` instead of `MCP_MEMORY_SERVER_URL`
3. `.env.example` - Updated with correct ARN format
4. `test_mcp_integration.py` - Fixed logger import and updated environment variable checks
5. `pyproject.toml` - Added boto3, botocore, and requests dependencies

## How to Test Locally

### Step 1: Verify Environment Variables

Make sure your `.env` file has:
```bash
MCP_MEMORY_SERVER_ARN="arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD"
AWS_REGION="us-east-1"
GROQ_API_KEY="your_groq_api_key"
```

### Step 2: Install Dependencies

```bash
cd Agents/agentcore-qna-specialist-agent
pip install boto3 botocore requests
```

Or use uv:
```bash
uv pip install boto3 botocore requests
```

### Step 3: Run the Test Script

```bash
python test_mcp_integration.py
```

This will run 4 test scenarios:
1. Single query without memory context
2. Multi-turn conversation with memory
3. Different sessions maintaining separate contexts
4. Error handling with invalid inputs

### Step 4: Expected Behavior

**Success indicators:**
- ✅ No 404 errors
- ✅ No "ModuleNotFoundError" errors
- ✅ `memory_used: True` when retrieving context
- ✅ `memory_stored: True` when storing interactions
- ✅ Agent responses that reference previous context in multi-turn conversations

**What to watch for:**
- AWS credentials will be used automatically from your environment
- Memory retrieval should return relevant past interactions
- Each session should maintain separate context

## How to Deploy

### Step 1: Deploy the Agent

```bash
cd Agents/agentcore-qna-specialist-agent
agentcore deploy
```

### Step 2: Launch with Environment Variables

```bash
agentcore launch \
  --env GROQ_API_KEY='your_groq_api_key' \
  --env MCP_MEMORY_SERVER_ARN="arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD" \
  --env AWS_REGION="us-east-1"
```

### Step 3: Test the Deployed Agent

```bash
agentcore invoke --prompt "What is roaming activation?" --actor-id "test-user" --session-id "test-session"
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'boto3'"

**Solution:** Install the required dependencies:
```bash
pip install boto3 botocore requests
```

### Issue: "Unable to locate credentials"

**Solution:** Verify your AWS credentials are configured:
```bash
aws configure
# or
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

### Issue: MCP server not responding

**Solution:** Verify the MCP server is deployed and running:
```bash
agentcore list-runtimes
```

Look for `agentcore_memory_mcp_server-R4jmV6ERZD` in the list.

### Issue: "403 Forbidden" or "AccessDeniedException"

**Solution:** Ensure your AWS credentials have permission to invoke the MCP server. You need this IAM policy:
```json
{
    "Effect": "Allow",
    "Action": "bedrock-agentcore:InvokeRuntime",
    "Resource": "arn:aws:bedrock-agentcore:*:*:runtime/*"
}
```

### Issue: Memory not being retrieved/stored

**Solution:** Check the logs for the specific error. Common causes:
- Incorrect ARN format
- MCP server not deployed with `--protocol MCP`
- AWS credentials don't have permission to invoke the MCP server
- Network connectivity issues

## Key Implementation Details

### JSON-RPC Protocol

The agent uses JSON-RPC 2.0 to call MCP tools:

```python
payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "retrieve_memory",
        "arguments": {
            "query": "user preferences",
            "max_results": 5,
            "actor_id": "user-123",
            "session_id": "session-456"
        }
    }
}
```

### AWS SigV4 Authentication

Each request is signed with AWS SigV4:

```python
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

request = AWSRequest(method="POST", url=invoke_url, data=body, headers=headers)
SigV4Auth(credentials, "bedrock-agentcore", region).add_auth(request)
```

### Response Format

The MCP server returns responses in SSE (Server-Sent Events) format:

```
data: {"jsonrpc":"2.0","id":1,"result":{...}}

```

The client automatically parses this format.

## Next Steps

1. ✅ Run local tests to verify the integration works
2. ✅ Deploy the updated agent to AWS
3. ✅ Test with real queries and verify memory persistence
4. ✅ Monitor logs for any errors or issues

## Reference Documentation

- See `MCP_JSONRPC_GUIDE.md` for detailed JSON-RPC implementation
- See `README_MCP_INTEGRATION.md` for architecture overview
- See `DEPLOYMENT_GUIDE.md` for deployment best practices
