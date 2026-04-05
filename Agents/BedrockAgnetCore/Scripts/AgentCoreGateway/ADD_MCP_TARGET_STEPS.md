# Step-by-Step: Add MCP Memory Server as Gateway Target

## Overview

This guide walks you through adding your MCP memory server (running on AgentCore runtime) as a target to an AgentCore Gateway.

**Your MCP Server:**
- ARN: `arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD`
- Tools: retrieve_memory, store_interaction, server_info

## Prerequisites

Before you start:
- ✅ MCP server deployed and running
- ✅ AWS credentials configured
- ✅ Access to AgentCore Gateway console/API
- ✅ IAM permissions for gateway operations

## Step 1: Verify MCP Server is Running

### Check Server Status

```bash
aws bedrock-agentcore get-runtime \
  --runtime-arn arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD \
  --region us-east-1
```

**Expected output:**
```json
{
  "runtimeArn": "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD",
  "status": "ACTIVE",
  "protocol": "MCP"
}
```

✅ If status is "ACTIVE", proceed to Step 2.
❌ If not found or inactive, deploy your server first.

### Test Server Connectivity

```bash
cd Scripts/AgentCoreGateway
python check_mcp_compatibility.py
```

This verifies:
- Server is reachable
- Tools are available
- Protocol is compatible

## Step 2: Apply Resource Policy to MCP Server

⚠️ **Critical:** The gateway cannot access your MCP server without a resource policy.

### Option A: Automatic (Try First)

```bash
cd Servers/agentcore-memory-mcp
python apply_gateway_policy.py
```

### Option B: Manual (If Automatic Fails)

The script will output a policy. Apply it manually:

1. **Go to AWS Console**
   - Navigate to: Bedrock → AgentCore → Runtimes
   - Find: `agentcore_memory_mcp_server-R4jmV6ERZD`
   - Click on the runtime

2. **Add Resource Policy**
   - Look for "Permissions" or "Resource Policy" tab
   - Click "Edit Policy" or "Add Policy"
   - Paste this policy:

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

3. **Save the policy**

### Verify Policy Applied

```bash
aws bedrock-agentcore get-runtime-resource-policy \
  --resource-arn arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD \
  --region us-east-1
```

✅ If you see the policy, proceed to Step 3.

## Step 3: Prepare Target Configuration

### Get the Configuration File

The configuration is ready in: `Scripts/AgentCoreGateway/mcp_endpoint_config.json`

```bash
cd Scripts/AgentCoreGateway
cat mcp_endpoint_config.json
```

### Key Values You'll Need

Copy these values (you'll use them in Step 4):

**Target Name:**
```
memory-mcp-server
```

**Target Type:**
```
MCP_SERVER
```

**Endpoint URL:**
```
https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD/runtime-endpoint/DEFAULT/invocations
```

**Protocol:**
```
MCP
```

**Protocol Version:**
```
2025-06-18
```

**Authentication:**
```
AWS_SIGV4
```

**Service:**
```
bedrock-agentcore
```

**Region:**
```
us-east-1
```

**Resource ARN:**
```
arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD
```

## Step 4: Add Target to Gateway

### Method A: AWS Console (Easiest)

1. **Navigate to Gateway**
   - Go to: AWS Console → Bedrock → AgentCore → Gateways
   - Select your gateway (or create one if needed)

2. **Add Target**
   - Click "Targets" tab
   - Click "Add Target" or "Create Target"

3. **Fill in Target Details**
   
   **Basic Information:**
   - Target Name: `memory-mcp-server`
   - Target Type: Select `MCP_SERVER` from dropdown
   - Description: `AgentCore Memory MCP Server for storing and retrieving conversation context`

4. **Configure Endpoint**
   
   **Endpoint Configuration:**
   - Endpoint URL: Paste the endpoint URL from Step 3
   - Protocol: Select `MCP`
   - Protocol Version: Select `2025-06-18` (or `2025-03-26` if that's what your server uses)

5. **Configure Authentication**
   
   **Authentication:**
   - Type: Select `AWS_SIGV4`
   - Service: `bedrock-agentcore`
   - Region: `us-east-1`

6. **Add Resource ARN**
   
   **Resource:**
   - Resource ARN: Paste the ARN from Step 3

7. **Add Tags (Optional)**
   
   **Tags:**
   - Environment: `production`
   - Service: `memory`
   - Protocol: `MCP`

8. **Review and Create**
   - Review all settings
   - Click "Create Target" or "Add Target"

### Method B: AWS CLI

```bash
aws bedrock-agentcore create-gateway-target \
  --gateway-id YOUR_GATEWAY_ID \
  --target-name memory-mcp-server \
  --target-type MCP_SERVER \
  --description "AgentCore Memory MCP Server" \
  --endpoint url=https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD/runtime-endpoint/DEFAULT/invocations,protocol=MCP,protocolVersion=2025-06-18 \
  --authentication type=AWS_SIGV4,service=bedrock-agentcore,region=us-east-1 \
  --resource-arn arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD \
  --region us-east-1
```

### Method C: Python SDK

```python
import boto3
import json

client = boto3.client('bedrock-agentcore', region_name='us-east-1')

# Load configuration
with open('mcp_endpoint_config.json', 'r') as f:
    config = json.load(f)

# Create target
response = client.create_gateway_target(
    gatewayId='YOUR_GATEWAY_ID',
    targetName=config['targetName'],
    targetType=config['targetType'],
    description=config['description'],
    endpoint=config['endpoint'],
    authentication=config['authentication'],
    resourceArn=config['resourceArn'],
    tags=config['tags']
)

print(f"✓ Target created: {response['targetId']}")
print(f"  Target ARN: {response['targetArn']}")
```

### Method D: Terraform

```hcl
resource "aws_bedrock_agentcore_gateway_target" "memory_mcp" {
  gateway_id  = var.gateway_id
  target_name = "memory-mcp-server"
  target_type = "MCP_SERVER"
  description = "AgentCore Memory MCP Server"

  endpoint {
    url              = "https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD/runtime-endpoint/DEFAULT/invocations"
    protocol         = "MCP"
    protocol_version = "2025-06-18"
  }

  authentication {
    type    = "AWS_SIGV4"
    service = "bedrock-agentcore"
    region  = "us-east-1"
  }

  resource_arn = "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD"

  tags = {
    Environment = "production"
    Service     = "memory"
    Protocol    = "MCP"
  }
}
```

Then apply:
```bash
terraform init
terraform plan
terraform apply
```

## Step 5: Verify Target is Added

### Check Target Status

```bash
aws bedrock-agentcore list-gateway-targets \
  --gateway-id YOUR_GATEWAY_ID \
  --region us-east-1
```

Look for your target in the list:
```json
{
  "targets": [
    {
      "targetId": "...",
      "targetName": "memory-mcp-server",
      "targetType": "MCP_SERVER",
      "status": "ACTIVE"
    }
  ]
}
```

✅ Status should be "ACTIVE"

### Get Target Details

```bash
aws bedrock-agentcore get-gateway-target \
  --gateway-id YOUR_GATEWAY_ID \
  --target-id TARGET_ID \
  --region us-east-1
```

## Step 6: Test the Target

### Test Tool Discovery

```bash
cd Scripts/AgentCoreGateway
python test_gateway.py
```

This will:
1. List available tools
2. Test server_info tool
3. Test store_interaction
4. Test retrieve_memory

**Expected output:**
```
✓ Found 3 tools:
  - retrieve_memory
  - store_interaction
  - server_info

✓ Server info retrieved
✓ Interaction stored
✓ Memory retrieved
```

### Test Individual Tool

```python
from agentcore_gateway import AgentCoreGateway

gateway = AgentCoreGateway(region='us-east-1')
gateway.register_server(
    name='memory',
    arn='arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD'
)

# Test server_info
result = gateway.invoke_mcp_tool(
    server_name='memory',
    tool_name='server_info',
    arguments={'session_id': 'test'}
)

print(result)
```

## Step 7: Configure Tool Access (Optional)

### Enable Tools for Agents

If you want agents to use these tools through the gateway:

1. **Go to Gateway Configuration**
   - Navigate to your gateway
   - Go to "Tools" or "Tool Configuration"

2. **Enable MCP Tools**
   - Find the memory-mcp-server target
   - Enable the tools you want agents to access:
     - ✅ retrieve_memory
     - ✅ store_interaction
     - ✅ server_info (for debugging)

3. **Set Tool Permissions**
   - Configure which agents can use which tools
   - Set rate limits if needed
   - Configure error handling

## Step 8: Use Target from Agent

### Update Your Agent

Now your agents can use the gateway to access the MCP server:

```python
# In your agent code
from agentcore_gateway import AgentCoreGateway

# Initialize gateway
gateway = AgentCoreGateway(region='us-east-1')
gateway.register_server(
    name='memory',
    arn='arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD'
)

# Use in your agent
def process_with_memory(query, actor_id, session_id):
    # Retrieve context
    memories = gateway.invoke_mcp_tool(
        server_name='memory',
        tool_name='retrieve_memory',
        arguments={
            'query': query,
            'max_results': 5,
            'actor_id': actor_id,
            'session_id': session_id
        }
    )
    
    # Process with agent...
    
    # Store interaction
    gateway.invoke_mcp_tool(
        server_name='memory',
        tool_name='store_interaction',
        arguments={
            'user_msg': query,
            'assistant_msg': response,
            'actor_id': actor_id,
            'session_id': session_id
        }
    )
```

## Troubleshooting

### Issue 1: 403 Forbidden

**Symptom:**
```
403 Client Error: Forbidden
```

**Solution:**
- Go back to Step 2
- Verify resource policy is applied
- Check IAM permissions

### Issue 2: 404 Not Found

**Symptom:**
```
404 Not Found
```

**Solution:**
- Verify MCP server ARN is correct
- Check server is deployed and running
- Verify endpoint URL format

### Issue 3: Connection Timeout

**Symptom:**
```
Connection timeout after 30s
```

**Solution:**
- Check server status: `aws bedrock-agentcore list-runtimes`
- Verify network configuration
- Check server logs in CloudWatch

### Issue 4: Protocol Version Mismatch

**Symptom:**
```
Protocol version not supported
```

**Solution:**
```bash
cd Scripts/AgentCoreGateway
python check_mcp_protocol_version.py
```

Update protocol version in target configuration to match server.

### Issue 5: Tools Not Found

**Symptom:**
```
No tools found
```

**Solution:**
- Verify MCP server is running
- Check server logs
- Test server directly: `python test_gateway.py`

## Verification Checklist

After completing all steps, verify:

- [ ] MCP server is running (Step 1)
- [ ] Resource policy applied (Step 2)
- [ ] Target configuration prepared (Step 3)
- [ ] Target added to gateway (Step 4)
- [ ] Target status is ACTIVE (Step 5)
- [ ] Tools are discoverable (Step 6)
- [ ] Tools can be invoked (Step 6)
- [ ] Agent can use target (Step 8)

## Next Steps

Once your target is working:

1. **Monitor Usage**
   - Check CloudWatch logs
   - Monitor invocation metrics
   - Track error rates

2. **Optimize Performance**
   - Add caching if needed
   - Configure timeouts
   - Set up retry logic

3. **Scale**
   - Add more MCP servers as targets
   - Configure load balancing
   - Set up failover

## Quick Reference

**MCP Server ARN:**
```
arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD
```

**Endpoint URL:**
```
https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD/runtime-endpoint/DEFAULT/invocations
```

**Test Command:**
```bash
cd Scripts/AgentCoreGateway
python test_gateway.py
```

## Support Files

- Configuration: `mcp_endpoint_config.json`
- Full guide: `MCP_ENDPOINT_CONFIGURATION.md`
- Quick ref: `MCP_ENDPOINT_QUICK_REF.md`
- Test script: `test_gateway.py`
- Policy script: `Servers/agentcore-memory-mcp/apply_gateway_policy.py`

## Summary

You've successfully added your MCP memory server as a gateway target! Your agents can now use the gateway to:
- Store conversation context
- Retrieve relevant memories
- Check server health

The gateway handles authentication, routing, and error handling automatically.
