#!/usr/bin/env python3
"""
Get Principal for Resource Policy

This script identifies the IAM principal (user/role) that should be added
to the MCP Memory Server resource policy.
"""

import boto3
import json
from botocore.exceptions import ClientError

def main():
    print("="*80)
    print("IAM Principal Identification for MCP Server Resource Policy")
    print("="*80)
    
    try:
        # Get caller identity
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        
        account = identity['Account']
        arn = identity['Arn']
        user_id = identity['UserId']
        
        print(f"\nYour AWS Identity:")
        print(f"  Account: {account}")
        print(f"  ARN: {arn}")
        print(f"  User ID: {user_id}")
        
        # Determine principal type
        if ':user/' in arn:
            principal_type = "IAM User"
            principal_arn = arn
        elif ':role/' in arn:
            principal_type = "IAM Role"
            # Extract the role ARN (remove session info if assumed role)
            if ':assumed-role/' in arn:
                role_name = arn.split('/')[-2]
                principal_arn = f"arn:aws:iam::{account}:role/{role_name}"
            else:
                principal_arn = arn
        elif ':root' in arn:
            principal_type = "Root Account"
            principal_arn = f"arn:aws:iam::{account}:root"
        else:
            principal_type = "Unknown"
            principal_arn = arn
        
        print(f"\nPrincipal Type: {principal_type}")
        print(f"Principal ARN: {principal_arn}")
        
        # Generate resource policy
        mcp_server_arn = "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD"
        
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowQNAAgentAccess",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": principal_arn
                    },
                    "Action": "bedrock-agentcore:InvokeRuntime",
                    "Resource": mcp_server_arn
                }
            ]
        }
        
        print("\n" + "="*80)
        print("RESOURCE POLICY TO ADD TO MCP SERVER")
        print("="*80)
        print(json.dumps(policy, indent=2))
        
        # Save to file
        with open('mcp_server_resource_policy.json', 'w') as f:
            json.dump(policy, f, indent=2)
        
        print("\n✓ Policy saved to: mcp_server_resource_policy.json")
        
        # Generate alternative policies
        print("\n" + "="*80)
        print("ALTERNATIVE POLICIES")
        print("="*80)
        
        # Option 1: All users in account
        policy_all_account = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowAllAccountUsers",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": f"arn:aws:iam::{account}:root"
                    },
                    "Action": "bedrock-agentcore:InvokeRuntime",
                    "Resource": mcp_server_arn
                }
            ]
        }
        
        print("\nOption 1: Allow all IAM principals in your account")
        print(json.dumps(policy_all_account, indent=2))
        
        with open('mcp_server_resource_policy_all_account.json', 'w') as f:
            json.dump(policy_all_account, f, indent=2)
        
        print("\n✓ Saved to: mcp_server_resource_policy_all_account.json")
        
        # Instructions
        print("\n" + "="*80)
        print("HOW TO APPLY THE POLICY")
        print("="*80)
        
        print("""
1. Using AgentCore CLI (if supported):
   agentcore update-runtime-policy \\
     --runtime-id agentcore_memory_mcp_server-R4jmV6ERZD \\
     --policy-document file://mcp_server_resource_policy.json

2. Using AWS Console:
   - Go to AWS Bedrock AgentCore console
   - Find runtime: agentcore_memory_mcp_server-R4jmV6ERZD
   - Navigate to Permissions/Resource Policy tab
   - Paste the policy JSON

3. Using AWS CLI (if supported):
   aws bedrock-agentcore put-runtime-policy \\
     --runtime-id agentcore_memory_mcp_server-R4jmV6ERZD \\
     --policy-document file://mcp_server_resource_policy.json \\
     --region us-east-1

4. Contact your AWS administrator if you don't have permission to update policies
        """)
        
        # Additional recommendations
        print("\n" + "="*80)
        print("RECOMMENDATIONS")
        print("="*80)
        
        if principal_type == "IAM User":
            print("""
✓ You're using an IAM User - this is good for development
✓ Use the specific user policy (mcp_server_resource_policy.json)
✓ For production, consider using an IAM Role instead
            """)
        elif principal_type == "IAM Role":
            print("""
✓ You're using an IAM Role - this is good for production
✓ Use the specific role policy (mcp_server_resource_policy.json)
✓ Make sure the role is attached to your agent runtime
            """)
        else:
            print("""
⚠ Consider using a specific IAM User or Role for better security
⚠ Avoid using root account credentials
            """)
        
    except ClientError as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure your AWS credentials are configured correctly:")
        print("  aws configure")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
