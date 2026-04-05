# Manual Resource Policy Application

## The Issue

You're getting 403 Forbidden errors because the MCP server doesn't have a resource policy allowing the gateway to invoke it.

## Solution: Apply Policy Manually

### Option 1: AWS Console (Easiest)

1. Go to AWS Console → Bedrock → AgentCore
2. Navigate to "Runtimes"
3. Find your runtime: `agentcore_memory_mcp_server-R4jmV6ERZD`
4. Click on it to open details
5. Look for "Permissions" or "Resource Policy" tab
6. Click "Edit Policy" or "Add Policy"
7. Paste this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowGatewayInvoke",
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock-agentcore.amazonaws.com"
      },
      "Action": [
        "bedrock-agentcore:InvokeRuntime",
        "bedrock-agentcore:InvokeAgentRuntime",
        "bedrock-agentcore:InvokeAgentRuntimeForUser"
      ],
      "Resource": [
        "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD",
        "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD/*"
      ],
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "662403250828"
        }
      }
    },
    {
      "Sid": "AllowAccountAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::662403250828:root"
      },
      "Action": [
        "bedrock-agentcore:InvokeRuntime",
        "bedrock-agentcore:InvokeAgentRuntime"
      ],
      "Resource": [
        "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD",
        "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD/*"
      ]
    }
  ]
}
```

8. Save the policy

### Option 2: AWS CLI (If Supported)

Try this command:

```bash
aws bedrock-agentcore put-runtime-resource-policy \
  --resource-arn arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD \
  --policy file://Servers/agentcore-memory-mcp/mcp_gateway_resource_policy.json \
  --region us-east-1
```

If that doesn't work, try:

```bash
aws bedrock-agentcore update-runtime \
  --runtime-arn arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD \
  --resource-policy file://Servers/agentcore-memory-mcp/mcp_gateway_resource_policy.json \
  --region us-east-1
```

### Option 3: Check IAM Permissions

The 403 might also be due to IAM permissions. Ensure your IAM user/role has:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:InvokeRuntime",
        "bedrock-agentcore:InvokeAgentRuntime",
        "bedrock-agentcore:GetRuntime",
        "bedrock-agentcore:ListRuntimes"
      ],
      "Resource": "*"
    }
  ]
}
```

## Workaround: Test with Your Agent's Credentials

Your agent (`03_agentcore_mcp_memory.py`) is already working, which means it has the right permissions. Try using the same credentials:

1. Check what credentials your agent uses
2. Use those same credentials in the gateway `.env` file
3. The gateway should then work

## Verify After Applying Policy

Run the test again:

```bash
cd Scripts/AgentCoreGateway
python test_gateway.py
```

You should see all tests pass ✓

## Alternative: Use Your Existing Agent Code

Since your agent's MCP client already works, you don't need to fix the gateway immediately. You can:

1. Keep using your current `MCPMemoryClient` in the agent
2. Apply the improvements from `FINAL_RECOMMENDATIONS.md` (retry logic, graceful degradation)
3. Come back to the gateway later when you need multiple MCP servers

The gateway is there when you need it, but your current implementation is working fine!
