# AWS Console Policy Setup Guide
## Adding Resource-Based Policies for AgentCore Gateway

This guide walks you through setting up resource-based policies via AWS Console to allow your AgentCore Gateway to invoke Lambda functions and Memory MCP servers.

---

## Part 1: Lambda Function Resource-Based Policy

### Step 1: Navigate to Lambda Function
1. Open AWS Console
2. Go to **Lambda** service
3. Select your Lambda function (e.g., `hello-lambda-tool`)

### Step 2: Add Resource-Based Policy
1. Click on the **Configuration** tab
2. Select **Permissions** from the left sidebar
3. Scroll down to **Resource-based policy statements**
4. Click **Add permissions**

### Step 3: Configure Permission
Choose **AWS service** and configure:
- **Service**: Select "Other"
- **Statement ID**: `AllowAgentCoreGatewayInvoke`
- **Principal**: `bedrock-agentcore.amazonaws.com`
- **Source ARN**: `arn:aws:bedrock-agentcore:REGION:ACCOUNT_ID:gateway/GATEWAY_NAME`
- **Action**: `lambda:InvokeFunction`
- Click **Save**

### Step 4: Add Account-Level Access (Optional)
1. Click **Add permissions** again
2. Choose **AWS account**
3. **AWS account ID**: Enter your account ID
4. **Statement ID**: `AllowAccountInvoke`
5. **Action**: `lambda:InvokeFunction`
6. Click **Save**

### Step 5: Verify Policy
Your Lambda resource-based policy should look like:
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
      "Resource": "arn:aws:lambda:REGION:ACCOUNT_ID:function:FUNCTION_NAME",
      "Condition": {
        "ArnLike": {
          "aws:SourceArn": "arn:aws:bedrock-agentcore:REGION:ACCOUNT_ID:gateway/*"
        }
      }
    }
  ]
}
```

---

## Part 2: Memory MCP Server Resource-Based Policy

### Step 1: Navigate to Bedrock AgentCore
1. Open AWS Console
2. Go to **Amazon Bedrock** service
3. In the left sidebar, find **AgentCore** section
4. Click on **Runtimes** or **MCP Servers**

### Step 2: Select Your MCP Server
1. Find your Memory MCP server (e.g., `agentcore_memory_mcp_server`)
2. Click on the server name to open details

### Step 3: Add Resource-Based Policy
1. Look for **Permissions** or **Resource-based policy** tab
2. Click **Edit** or **Add policy**
3. Paste the following policy (replace placeholders):

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
        "bedrock-agentcore:InvokeAgentRuntime"
      ],
      "Resource": "arn:aws:bedrock-agentcore:REGION:ACCOUNT_ID:runtime/MCP_SERVER_NAME",
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "ACCOUNT_ID"
        }
      }
    }
  ]
}
```

4. Click **Save changes**

---

## Part 3: AgentCore Gateway Resource-Based Policy

### Step 1: Navigate to Your Gateway
1. In AWS Console, go to **Amazon Bedrock**
2. Navigate to **AgentCore** → **Gateways**
3. Select your gateway

### Step 2: Add Resource-Based Policy to Gateway
1. Click on **Permissions** or **Resource-based policy** tab
2. Click **Add** or **Edit policy**
3. Add the following policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowGatewayInvokeLambda",
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock-agentcore.amazonaws.com"
      },
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": [
        "arn:aws:lambda:REGION:ACCOUNT_ID:function:FUNCTION_NAME"
      ]
    },
    {
      "Sid": "AllowGatewayInvokeMCP",
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock-agentcore.amazonaws.com"
      },
      "Action": [
        "bedrock-agentcore:InvokeRuntime",
        "bedrock-agentcore:InvokeAgentRuntime"
      ],
      "Resource": [
        "arn:aws:bedrock-agentcore:REGION:ACCOUNT_ID:runtime/MCP_SERVER_NAME"
      ]
    }
  ]
}
```

---

## Part 4: IAM Execution Role for Gateway

### Step 1: Create/Update IAM Role
1. Go to **IAM** service in AWS Console
2. Click **Roles** in the left sidebar
3. Find your AgentCore Gateway execution role or click **Create role**

### Step 2: Configure Trust Relationship
1. Select the role
2. Go to **Trust relationships** tab
3. Click **Edit trust policy**
4. Ensure it includes:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock-agentcore.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### Step 3: Attach Permissions Policy
1. Go to **Permissions** tab
2. Click **Add permissions** → **Create inline policy**
3. Switch to **JSON** tab
4. Paste the policy from `iam_execution_role_policy.json`
5. Name it: `AgentCoreGatewayExecutionPolicy`
6. Click **Create policy**

---

## Part 5: Configure Gateway to Use Targets

### Step 1: Add Lambda as Target
1. In your AgentCore Gateway console
2. Go to **Targets** or **Tools** section
3. Click **Add target**
4. Configure:
   - **Type**: Lambda Function
   - **Function ARN**: `arn:aws:lambda:REGION:ACCOUNT_ID:function:FUNCTION_NAME`
   - **Tool Name**: `DefaultTool`
   - **Description**: Default tool description
   - **Input Schema**: `{}`

### Step 2: Add MCP Server as Target
1. Click **Add target** again
2. Configure:
   - **Type**: MCP Server
   - **Server ARN**: `arn:aws:bedrock-agentcore:REGION:ACCOUNT_ID:runtime/MCP_SERVER_NAME`
   - **Tool Name**: Memory tools (auto-discovered)

### Step 3: Save Configuration
1. Review all targets
2. Click **Save** or **Update gateway**

---

## Part 6: Testing the Setup

### Test Lambda Invocation
```bash
aws bedrock-agentcore invoke-gateway \
  --gateway-identifier "GATEWAY_ARN" \
  --tool-name "DefaultTool" \
  --tool-input '{}' \
  --region REGION
```

### Test MCP Server Invocation
```bash
aws bedrock-agentcore invoke-runtime \
  --runtime-identifier "MCP_SERVER_ARN" \
  --action "list_tools" \
  --region REGION
```

---

## Troubleshooting

### Error: Access Denied (403)
- Verify resource-based policies are correctly applied
- Check IAM role has necessary permissions
- Ensure source account condition matches
- Verify ARNs are correct

### Error: Lambda Not Invoked
- Check Lambda resource-based policy includes bedrock-agentcore.amazonaws.com
- Verify Lambda function is in the same region
- Check CloudWatch logs for Lambda

### Error: MCP Server Not Found
- Verify MCP server is deployed and active
- Check server ARN is correct
- Ensure resource-based policy is attached to server

---

## Quick Reference: Replace These Placeholders

- `REGION`: Your AWS region (e.g., `us-east-1`)
- `ACCOUNT_ID`: Your AWS account ID (e.g., `662403250828`)
- `FUNCTION_NAME`: Your Lambda function name (e.g., `hello-lambda-tool`)
- `GATEWAY_NAME`: Your AgentCore gateway name
- `MCP_SERVER_NAME`: Your MCP server runtime name (e.g., `agentcore_memory_mcp_server-R4jmV6ERZD`)

---

## Summary Checklist

- [ ] Lambda resource-based policy added
- [ ] MCP server resource-based policy added
- [ ] Gateway resource-based policy configured
- [ ] IAM execution role created/updated
- [ ] Trust relationship configured
- [ ] Lambda target added to gateway
- [ ] MCP server target added to gateway
- [ ] Tested Lambda invocation
- [ ] Tested MCP server invocation

---

**Note**: Some UI elements may vary depending on AWS Console version. If you can't find specific options, use the AWS CLI commands provided in the testing section.
