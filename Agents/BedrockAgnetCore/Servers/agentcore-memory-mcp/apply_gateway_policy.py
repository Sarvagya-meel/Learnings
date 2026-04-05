#!/usr/bin/env python3
"""
Apply Gateway Resource Policy to MCP Memory Server

This script applies a resource policy to the MCP memory server runtime
that allows the AgentCore Gateway to invoke it.
"""

import boto3
import json
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configuration
MCP_SERVER_RUNTIME_ARN = "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD"
REGION = "us-east-1"
ACCOUNT_ID = "662403250828"

# Get AWS credentials
ACCESS_KEY = os.getenv("AGENTCORE_ACCESS_KEY")
SECRET_KEY = os.getenv("AGENTCORE_SECRET_KEY")

def create_gateway_policy():
    """Create a resource policy that allows gateway to invoke MCP server"""
    policy = {
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
                    "bedrock-agentcore:InvokeAgentRuntimeForUser",
                    "bedrock-agentcore:GetAgentCard"
                ],
                "Resource": [
                    MCP_SERVER_RUNTIME_ARN,
                    f"{MCP_SERVER_RUNTIME_ARN}/*"
                ],
                "Condition": {
                    "StringEquals": {
                        "aws:SourceAccount": ACCOUNT_ID
                    }
                }
            },
            {
                "Sid": "AllowAccountAccess",
                "Effect": "Allow",
                "Principal": {
                    "AWS": f"arn:aws:iam::{ACCOUNT_ID}:root"
                },
                "Action": [
                    "bedrock-agentcore:InvokeRuntime",
                    "bedrock-agentcore:InvokeAgentRuntime",
                    "bedrock-agentcore:InvokeAgentRuntimeForUser"
                ],
                "Resource": [
                    MCP_SERVER_RUNTIME_ARN,
                    f"{MCP_SERVER_RUNTIME_ARN}/*"
                ]
            }
        ]
    }
    return policy

def apply_policy_via_api():
    """Attempt to apply the policy using boto3"""
    try:
        # Create boto3 client
        session = boto3.Session(
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
            region_name=REGION
        )
        
        client = session.client('bedrock-agentcore')
        
        policy = create_gateway_policy()
        policy_json = json.dumps(policy)
        
        print("Attempting to apply resource policy via API...")
        
        # Try to put the resource policy
        response = client.put_runtime_resource_policy(
            resourceArn=MCP_SERVER_RUNTIME_ARN,
            policy=policy_json
        )
        
        print("✓ Policy applied successfully!")
        print(f"Response: {json.dumps(response, indent=2, default=str)}")
        return True
        
    except AttributeError:
        print("⚠ API method 'put_runtime_resource_policy' not available in boto3")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        print(f"❌ AWS API Error: {error_code}")
        print(f"   Message: {error_msg}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("="*80)
    print("Apply Gateway Resource Policy to MCP Memory Server")
    print("="*80)
    
    policy = create_gateway_policy()
    
    # Save policy to file
    policy_file = "mcp_gateway_resource_policy.json"
    with open(policy_file, 'w') as f:
        json.dump(policy, f, indent=2)
    
    print(f"\n✓ Policy saved to: {policy_file}")
    print("\nPolicy content:")
    print(json.dumps(policy, indent=2))
    
    # Try to apply via API
    print("\n" + "="*80)
    print("Attempting to Apply Policy via API")
    print("="*80)
    
    success = apply_policy_via_api()
    
    if not success:
        print("\n" + "="*80)
        print("Manual Application Required")
        print("="*80)
        print("""
The policy could not be applied automatically. Please apply it manually:

METHOD 1: AWS Console
----------------------
1. Go to AWS Bedrock AgentCore Console
2. Navigate to: Runtimes
3. Find runtime: agentcore_memory_mcp_server-R4jmV6ERZD
4. Click on the runtime to open details
5. Go to "Permissions" or "Resource Policy" tab
6. Click "Edit" or "Add Policy"
7. Paste the policy from: mcp_gateway_resource_policy.json
8. Save the policy

METHOD 2: AWS CLI (if supported)
---------------------------------
aws bedrock-agentcore put-runtime-resource-policy \\
  --resource-arn arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD \\
  --policy file://mcp_gateway_resource_policy.json \\
  --region us-east-1

METHOD 3: AgentCore CLI (if supported)
---------------------------------------
agentcore update-runtime-policy \\
  --runtime-arn arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD \\
  --policy-document file://mcp_gateway_resource_policy.json
        """)
    
    print("\n" + "="*80)
    print("What This Policy Does")
    print("="*80)
    print("""
Statement 1 (AllowGatewayInvoke):
  ✓ Allows bedrock-agentcore service to invoke your MCP server
  ✓ Includes all necessary actions for gateway operation
  ✓ Covers both the runtime and its endpoints (/*) 
  ✓ Restricted to your AWS account for security

Statement 2 (AllowAccountAccess):
  ✓ Allows all IAM users/roles in your account to invoke
  ✓ Enables direct testing and agent access
  ✓ Covers runtime and endpoints

After applying this policy, the gateway should be able to:
  - Connect to your MCP memory server
  - Fetch available tools
  - Invoke tools on behalf of agents
    """)
    
    print("\n" + "="*80)
    print("Next Steps")
    print("="*80)
    print("""
1. Apply the policy using one of the methods above
2. Verify the policy is attached to the runtime
3. Try adding the target to the gateway again with endpoint:
   
   https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD/runtime-endpoint/DEFAULT/invocations

4. Check gateway logs if connection still fails
    """)

if __name__ == "__main__":
    main()
