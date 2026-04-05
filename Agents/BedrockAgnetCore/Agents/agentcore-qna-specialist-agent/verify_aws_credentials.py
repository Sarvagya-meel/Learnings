#!/usr/bin/env python3
"""
AWS Credentials Verification Script

This script helps diagnose 403 Forbidden errors by checking:
1. Environment variables are set correctly
2. Boto3 can load credentials
3. AWS account matches expected account
4. IAM permissions are correct
"""

import os
import sys
import boto3
from dotenv import load_dotenv
from botocore.exceptions import ClientError, NoCredentialsError

# Colors for output
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"

def print_success(msg):
    print(f"{GREEN}✓ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}✗ {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠ {msg}{RESET}")

def print_header(msg):
    print(f"\n{'='*80}")
    print(f"{msg}")
    print(f"{'='*80}\n")

# Load environment variables
load_dotenv()

print_header("AWS Credentials Verification")

# Expected values
EXPECTED_ACCOUNT = "662403250828"
EXPECTED_REGION = "us-east-1"
MCP_SERVER_ARN = "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD"

# Step 1: Check environment variables
print_header("Step 1: Environment Variables")

aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION")

if aws_access_key:
    print_success(f"AWS_ACCESS_KEY_ID is set: {aws_access_key[:8]}...")
else:
    print_error("AWS_ACCESS_KEY_ID is NOT set")

if aws_secret_key:
    print_success(f"AWS_SECRET_ACCESS_KEY is set: {'*' * 20}")
else:
    print_error("AWS_SECRET_ACCESS_KEY is NOT set")

if aws_region:
    print_success(f"AWS_REGION is set: {aws_region}")
    if aws_region != EXPECTED_REGION:
        print_warning(f"Region mismatch! Expected: {EXPECTED_REGION}, Got: {aws_region}")
else:
    print_warning(f"AWS_REGION is NOT set (will use default)")

# Step 2: Check boto3 credentials
print_header("Step 2: Boto3 Credentials")

try:
    session = boto3.Session()
    credentials = session.get_credentials()
    
    if credentials:
        print_success(f"Boto3 found credentials")
        print(f"  Access Key: {credentials.access_key[:8]}...")
        print(f"  Secret Key: {'*' * 20}")
        
        # Check if they match environment variables
        if aws_access_key and credentials.access_key != aws_access_key:
            print_warning("Boto3 credentials don't match environment variables!")
            print(f"  Env: {aws_access_key[:8]}...")
            print(f"  Boto3: {credentials.access_key[:8]}...")
    else:
        print_error("Boto3 could NOT find credentials")
        sys.exit(1)
        
except NoCredentialsError:
    print_error("No credentials found by boto3")
    sys.exit(1)
except Exception as e:
    print_error(f"Error loading credentials: {e}")
    sys.exit(1)

# Step 3: Verify AWS account
print_header("Step 3: AWS Account Verification")

try:
    sts = boto3.client('sts', region_name=aws_region or EXPECTED_REGION)
    identity = sts.get_caller_identity()
    
    account = identity['Account']
    user_arn = identity['Arn']
    user_id = identity['UserId']
    
    print_success(f"Successfully authenticated with AWS")
    print(f"  Account: {account}")
    print(f"  User ARN: {user_arn}")
    print(f"  User ID: {user_id}")
    
    if account == EXPECTED_ACCOUNT:
        print_success(f"Account matches expected: {EXPECTED_ACCOUNT}")
    else:
        print_error(f"Account mismatch!")
        print(f"  Expected: {EXPECTED_ACCOUNT}")
        print(f"  Got: {account}")
        print_warning("You're using credentials from the wrong AWS account!")
        
except ClientError as e:
    error_code = e.response['Error']['Code']
    error_msg = e.response['Error']['Message']
    print_error(f"AWS API Error: {error_code}")
    print(f"  Message: {error_msg}")
    
    if error_code == 'InvalidClientTokenId':
        print_error("Your AWS Access Key ID is invalid")
    elif error_code == 'SignatureDoesNotMatch':
        print_error("Your AWS Secret Access Key is invalid")
    
    sys.exit(1)
except Exception as e:
    print_error(f"Error verifying account: {e}")
    sys.exit(1)

# Step 4: Check IAM permissions
print_header("Step 4: IAM Permissions Check")

print("Checking if you can list AgentCore runtimes...")

try:
    # Try to list runtimes (this requires bedrock-agentcore:ListRuntimes permission)
    # Note: This is a placeholder - the actual API call depends on AgentCore CLI
    print_warning("Cannot programmatically check IAM permissions")
    print("Please run manually: agentcore list-runtimes")
    
except Exception as e:
    print_warning(f"Could not check permissions: {e}")

# Step 5: Test MCP server invocation
print_header("Step 5: MCP Server Invocation Test")

print(f"MCP Server ARN: {MCP_SERVER_ARN}")
print("\nAttempting to invoke MCP server...")

try:
    from urllib.parse import quote
    import requests
    from botocore.auth import SigV4Auth
    from botocore.awsrequest import AWSRequest
    import json
    
    # Build URL
    encoded_arn = quote(MCP_SERVER_ARN, safe='')
    invoke_url = f"https://bedrock-agentcore.{aws_region or EXPECTED_REGION}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
    
    print(f"Invoke URL: {invoke_url}")
    
    # Prepare JSON-RPC request
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    body = json.dumps(payload).encode("utf-8")
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    # Sign request
    request = AWSRequest(method="POST", url=invoke_url, data=body, headers=headers)
    SigV4Auth(credentials, "bedrock-agentcore", aws_region or EXPECTED_REGION).add_auth(request)
    
    # Make request
    response = requests.post(
        invoke_url,
        headers=dict(request.headers),
        data=body,
        timeout=10
    )
    
    print(f"\nResponse Status: {response.status_code}")
    
    if response.status_code == 200:
        print_success("Successfully invoked MCP server!")
        print("\nResponse preview:")
        print(response.text[:500])
    elif response.status_code == 403:
        print_error("403 Forbidden - Permission denied")
        print("\nPossible causes:")
        print("  1. Missing IAM permission: bedrock-agentcore:InvokeRuntime")
        print("  2. Wrong AWS account (credentials from different account)")
        print("  3. MCP server not deployed or wrong ARN")
        print("\nRequired IAM policy:")
        print("""
{
    "Effect": "Allow",
    "Action": "bedrock-agentcore:InvokeRuntime",
    "Resource": "arn:aws:bedrock-agentcore:*:*:runtime/*"
}
        """)
    elif response.status_code == 404:
        print_error("404 Not Found - MCP server doesn't exist")
        print("\nPlease deploy the MCP server first:")
        print("  cd Servers/agentcore-memory-mcp")
        print("  agentcore deploy")
    else:
        print_error(f"Unexpected status code: {response.status_code}")
        print(f"Response: {response.text}")
    
except Exception as e:
    print_error(f"Error invoking MCP server: {e}")
    import traceback
    traceback.print_exc()

# Summary
print_header("Summary")

if account == EXPECTED_ACCOUNT and credentials:
    print_success("Credentials are configured correctly")
    print("\nIf you're still getting 403 errors, the issue is likely:")
    print("  1. Missing IAM permissions")
    print("  2. MCP server not deployed")
    print("\nNext steps:")
    print("  1. Run: agentcore list-runtimes")
    print("  2. Check IAM permissions with your AWS administrator")
    print("  3. See TROUBLESHOOT_403.md for detailed troubleshooting")
else:
    print_error("Credentials are NOT configured correctly")
    print("\nPlease fix the issues above and try again")

print()
