#!/usr/bin/env python3
"""
Add Gateway Resource Policy to MCP Server

This script adds a resource policy to the MCP server runtime that allows
the AgentCore Gateway to invoke it.
"""

import boto3
import json
from botocore.exceptions import ClientError

# Configuration
MCP_SERVER_ARN = "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD"
REGION = "us-east-1"
ACCOUNT_ID = "662403250828"

def main():
    print("="*80)
    print("Adding Gateway Resource Policy to MCP Server")
    print("="*80)
    
    # Policy that allows the gateway service to invoke the runtime
    # The gateway uses the account's service principal
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowGatewayAccess",
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock-agentcore.amazonaws.com"
                },
                "Action": "bedrock-agentcore:InvokeRuntime",
                "Resource": MCP_SERVER_ARN,
                "Condition": {
                    "StringEquals": {
                        "aws:SourceAccount": ACCOUNT_ID
                    }
                }
            },
            {
                "Sid": "AllowUserAccess",
                "Effect": "Allow",
                "Principal": {
                    "AWS": f"arn:aws:iam::{ACCOUNT_ID}:root"
                },
                "Action": "bedrock-agentcore:InvokeRuntime",
                "Resource": MCP_SERVER_ARN
            }
        ]
    }
    
    print("\nResource Policy to Apply:")
    print(json.dumps(policy, indent=2))
    
    # Save to file
    policy_file = "mcp_server_gateway_policy.json"
    with open(policy_file, 'w') as f:
        json.dump(policy, f, indent=2)
    
    print(f"\n✓ Policy saved to: {policy_file}")
    
    print("\n" + "="*80)
    print("HOW TO APPLY THIS POLICY")
    print("="*80)
    
    print("""
Option 1: Using AWS Console
----------------------------
1. Go to AWS Bedrock AgentCore console
2. Navigate to Runtimes
3. Find runtime: agentcore_memory_mcp_server-R4jmV6ERZD
4. Go to Permissions or Resource Policy tab
5. Paste the policy JSON from mcp_server_gateway_policy.json

Option 2: Using AWS CLI (if the API is available)
--------------------------------------------------
aws bedrock-agentcore put-runtime-resource-policy \\
  --resource-arn arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD \\
  --policy file://mcp_server_gateway_policy.json \\
  --region us-east-1

Option 3: Using AgentCore CLI (if supported)
---------------------------------------------
agentcore update-runtime-policy \\
  --runtime-id agentcore_memory_mcp_server-R4jmV6ERZD \\
  --policy-document file://mcp_server_gateway_policy.json

After applying the policy, try adding the target to the gateway again.
    """)
    
    print("\n" + "="*80)
    print("WHAT THIS POLICY DOES")
    print("="*80)
    print("""
Statement 1 (AllowGatewayAccess):
  - Allows the bedrock-agentcore service to invoke your MCP server
  - Restricted to your AWS account for security
  - This is what the gateway needs to connect to your MCP server

Statement 2 (AllowUserAccess):
  - Allows all IAM users/roles in your account to invoke the server
  - Enables your direct testing and agent access
  - Uses account root principal for simplicity
    """)

if __name__ == "__main__":
    main()
