#!/bin/bash

# Script to apply resource-based policies via AWS CLI
# Use this if AWS Console doesn't have the UI options

set -e

# Configuration - UPDATE THESE VALUES
REGION="us-east-1"
ACCOUNT_ID="662403250828"
LAMBDA_FUNCTION_NAME="hello-lambda-tool"
MCP_SERVER_NAME="agentcore_memory_mcp_server-R4jmV6ERZD"
GATEWAY_NAME="your-gateway-name"

echo "=== Applying Resource-Based Policies ==="
echo "Region: $REGION"
echo "Account: $ACCOUNT_ID"
echo ""

# 1. Add Lambda Resource-Based Policy
echo "1. Adding Lambda resource-based policy..."
aws lambda add-permission \
  --function-name "$LAMBDA_FUNCTION_NAME" \
  --statement-id "AllowAgentCoreGatewayInvoke" \
  --action "lambda:InvokeFunction" \
  --principal "bedrock-agentcore.amazonaws.com" \
  --source-account "$ACCOUNT_ID" \
  --region "$REGION"

echo "✓ Lambda policy added"
echo ""

# 2. Add Lambda Account Access
echo "2. Adding Lambda account access..."
aws lambda add-permission \
  --function-name "$LAMBDA_FUNCTION_NAME" \
  --statement-id "AllowAccountInvoke" \
  --action "lambda:InvokeFunction" \
  --principal "$ACCOUNT_ID" \
  --region "$REGION"

echo "✓ Lambda account access added"
echo ""

# 3. Verify Lambda Policy
echo "3. Verifying Lambda policy..."
aws lambda get-policy \
  --function-name "$LAMBDA_FUNCTION_NAME" \
  --region "$REGION" \
  --query 'Policy' \
  --output text | jq .

echo ""

# 4. Add MCP Server Resource-Based Policy (if API available)
echo "4. Adding MCP server resource-based policy..."
echo "Note: This may require using AWS Console or specific AgentCore CLI"
echo "MCP Server ARN: arn:aws:bedrock-agentcore:$REGION:$ACCOUNT_ID:runtime/$MCP_SERVER_NAME"
echo ""

# Create policy file for manual application
cat > /tmp/mcp_policy.json <<EOF
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
      "Resource": "arn:aws:bedrock-agentcore:$REGION:$ACCOUNT_ID:runtime/$MCP_SERVER_NAME",
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "$ACCOUNT_ID"
        }
      }
    }
  ]
}
EOF

echo "MCP policy saved to /tmp/mcp_policy.json"
echo "Apply this manually via AWS Console to the MCP server"
echo ""

# 5. Test Lambda Invocation
echo "5. Testing Lambda invocation..."
aws lambda invoke \
  --function-name "$LAMBDA_FUNCTION_NAME" \
  --payload '{"toolName":"DefaultTool","toolInput":{}}' \
  --region "$REGION" \
  /tmp/lambda_response.json

echo "Lambda response:"
cat /tmp/lambda_response.json | jq .
echo ""

echo "=== Policy Application Complete ==="
echo ""
echo "Next steps:"
echo "1. Apply MCP server policy via AWS Console"
echo "2. Configure gateway targets in AgentCore console"
echo "3. Test gateway invocation"
