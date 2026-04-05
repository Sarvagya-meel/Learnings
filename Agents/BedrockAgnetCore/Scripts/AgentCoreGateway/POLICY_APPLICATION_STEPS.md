# Step-by-Step Policy Application Guide

## The Problem with Your Original Policy

Your policy had these issues:
1. Mixed Lambda and AgentCore actions in the same statement
2. Extra `::` in the MCP server ARN (should be single `:`)
3. Lambda actions don't belong in gateway resource-based policy

## Correct Approach: Apply 3 Separate Policies

---

## Step 1: Apply Lambda Resource-Based Policy

**Where**: Lambda Function Console → Configuration → Permissions → Resource-based policy

**Policy to Apply**: `lambda_policy_separate.json`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowAgentCoreGatewayInvoke",
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock-agentcore.amazonaws.com"
      },
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:us-east-1:662403250828:function:hello_lambda_tool",
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "662403250828"
        }
      }
    }
  ]
}
```

**Via AWS Console**:
1. Go to Lambda → Functions → `hello_lambda_tool`
2. Configuration tab → Permissions
3. Scroll to "Resource-based policy statements"
4. Click "Add permissions"
5. Select:
   - Service: Other
   - Statement ID: `AllowAgentCoreGatewayInvoke`
   - Principal: `bedrock-agentcore.amazonaws.com`
   - Action: `lambda:InvokeFunction`
   - Source account: `662403250828`
6. Save

**Via AWS CLI**:
```bash
aws lambda add-permission \
  --function-name hello_lambda_tool \
  --statement-id AllowAgentCoreGatewayInvoke \
  --action lambda:InvokeFunction \
  --principal bedrock-agentcore.amazonaws.com \
  --source-account 662403250828 \
  --region us-east-1
```

---

## Step 2: Apply MCP Server Resource-Based Policy

**Where**: Bedrock AgentCore Console → Runtimes → Your MCP Server → Permissions

**Policy to Apply**: `mcp_server_policy_corrected.json`

**Important**: Note the ARN has single `:` not `::`
- ✅ Correct: `arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD`
- ❌ Wrong: `arn:aws:bedrock-agentcore:us-east-1:662403250828::runtime/...`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowGatewayInvokeMCP",
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock-agentcore.amazonaws.com"
      },
      "Action": [
        "bedrock-agentcore:InvokeRuntime",
        "bedrock-agentcore:InvokeAgentRuntime",
        "bedrock-agentcore:InvokeAgentRuntimeForUser"
      ],
      "Resource": "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD",
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
      "Resource": "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD"
    }
  ]
}
```

**Via AWS Console**:
1. Go to Bedrock → AgentCore → Runtimes
2. Select `agentcore_memory_mcp_server-R4jmV6ERZD`
3. Click "Permissions" or "Resource-based policy" tab
4. Click "Edit" and paste the policy above
5. Save

**Via Python Script**:
```bash
cd Servers/agentcore-memory-mcp
python add_gateway_resource_policy.py
```

---

## Step 3: Apply Gateway Resource-Based Policy (Optional)

**Where**: Bedrock AgentCore Console → Gateways → Your Gateway → Permissions

**Policy to Apply**: `gateway_resource_policy_corrected.json`

This policy allows the gateway itself to be invoked.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowBedrockAgentCoreService",
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock-agentcore.amazonaws.com"
      },
      "Action": [
        "bedrock-agentcore:InvokeGateway"
      ],
      "Resource": "arn:aws:bedrock-agentcore:us-east-1:662403250828:gateway/*",
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
        "bedrock-agentcore:InvokeGateway"
      ],
      "Resource": "arn:aws:bedrock-agentcore:us-east-1:662403250828:gateway/*"
    }
  ]
}
```

---

## Step 4: Configure Gateway Execution Role

The gateway also needs an IAM execution role with permissions to invoke targets.

**Where**: IAM Console → Roles → Your Gateway Execution Role

**Policy to Attach**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": [
        "arn:aws:lambda:us-east-1:662403250828:function:hello_lambda_tool"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:InvokeRuntime",
        "bedrock-agentcore:InvokeAgentRuntime"
      ],
      "Resource": [
        "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD"
      ]
    }
  ]
}
```

---

## Summary: What Goes Where

| Policy Type | Applied To | Purpose |
|------------|-----------|---------|
| Lambda Resource-Based | Lambda Function | Allows AgentCore to invoke Lambda |
| MCP Resource-Based | MCP Server Runtime | Allows Gateway to invoke MCP server |
| Gateway Resource-Based | Gateway | Allows invocation of the gateway itself |
| IAM Execution Role | IAM Role | Gives gateway permissions to call targets |

---

## Common Errors and Fixes

### Error: "An error occurred while processing the policy"

**Causes**:
1. Mixed service actions in same statement
2. Invalid ARN format (extra colons)
3. Wrong resource type for action

**Fix**: Use separate policies for each resource type

### Error: "Invalid principal"

**Cause**: Wrong service principal name

**Fix**: Use exact service name: `bedrock-agentcore.amazonaws.com`

### Error: "Resource ARN is invalid"

**Cause**: Extra `::` in ARN or wrong format

**Fix**: 
- ✅ `arn:aws:bedrock-agentcore:region:account:runtime/name`
- ❌ `arn:aws:bedrock-agentcore:region:account::runtime/name`

---

## Verification Commands

### Verify Lambda Policy
```bash
aws lambda get-policy \
  --function-name hello_lambda_tool \
  --region us-east-1 \
  --query Policy --output text | jq
```

### Test Lambda Invocation
```bash
aws lambda invoke \
  --function-name hello_lambda_tool \
  --payload '{"toolName":"DefaultTool","toolInput":{}}' \
  --region us-east-1 \
  response.json && cat response.json
```

### Test MCP Server
```bash
aws bedrock-agentcore invoke-runtime \
  --runtime-identifier agentcore_memory_mcp_server-R4jmV6ERZD \
  --region us-east-1
```

---

## Quick Fix Script

Run this to apply all policies via CLI:

```bash
cd Scripts/AgentCoreGateway
chmod +x apply_policies_cli.sh
./apply_policies_cli.sh
```
