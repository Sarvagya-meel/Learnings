# AgentCore Gateway Target Configuration Guide

## Understanding the Validation Errors

The errors you encountered indicate:
1. **Missing required fields**: `name`, `description`, `inputSchema` must all be present
2. **Name pattern constraint**: Gateway name must match `([0-9a-zA-Z][-]?){1,100}` (alphanumeric with optional hyphens)
3. **Null values**: All required fields must have non-null values
4. **Wrong structure**: The configuration structure wasn't matching AgentCore's expected format

---

## Correct Configuration Format

### For Lambda Target

```json
{
  "name": "hello-lambda-gateway",
  "targetConfiguration": {
    "lambda": {
      "lambdaArn": "arn:aws:lambda:us-east-1:662403250828:function:hello_lambda_tool",
      "toolSchema": {
        "inlinePayload": [
          {
            "name": "DefaultTool",
            "description": "Default tool that returns a greeting message from Lambda",
            "inputSchema": {
              "json": {
                "type": "object",
                "properties": {}
              }
            }
          }
        ]
      }
    }
  }
}
```

### For MCP Server Target

```json
{
  "name": "memory-mcp-gateway",
  "targetConfiguration": {
    "mcp": {
      "mcpServerArn": "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD"
    }
  }
}
```

---

## Step-by-Step: Add Lambda Target via AWS Console

### Step 1: Navigate to Gateway
1. Open AWS Console → Amazon Bedrock
2. Go to AgentCore → Gateways
3. Select your gateway or create a new one
4. Gateway name must be: `hello-lambda-gateway` (alphanumeric with hyphens only)

### Step 2: Add Lambda Target
1. Click "Add target" or "Configure targets"
2. Select target type: **Lambda**
3. Fill in the form:

**Target Configuration:**
- **Target name**: `lambda-target-1`
- **Lambda ARN**: `arn:aws:lambda:us-east-1:662403250828:function:hello_lambda_tool`

**Tool Schema:**
- **Schema type**: Inline
- Click "Add tool"

**Tool Details (REQUIRED - all fields must be filled):**
- **Tool name**: `DefaultTool` (no spaces, alphanumeric)
- **Tool description**: `Default tool that returns a greeting message from Lambda`
- **Input schema**: 
  ```json
  {
    "type": "object",
    "properties": {}
  }
  ```

### Step 3: Save Target
1. Click "Add tool" to confirm the tool
2. Click "Save target" to add the Lambda target
3. Verify the target appears in the gateway configuration

---

## Step-by-Step: Add MCP Server Target via AWS Console

### Step 1: In Same Gateway
1. Stay in your gateway configuration
2. Click "Add target" again

### Step 2: Add MCP Target
1. Select target type: **MCP Server**
2. Fill in:
   - **Target name**: `mcp-target-1`
   - **MCP Server ARN**: `arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD`

### Step 3: Save Target
1. Click "Save target"
2. MCP tools will be auto-discovered from the server
3. Verify both targets are now configured

---

## Common Validation Errors and Fixes

### Error: "Member must not be null"
**Cause**: Required field is missing or empty

**Fix**: Ensure all these fields are filled:
- `name` ✓
- `description` ✓
- `inputSchema` ✓

### Error: "Member must satisfy regular expression pattern"
**Cause**: Gateway or tool name contains invalid characters

**Fix**: Use only:
- Letters (a-z, A-Z)
- Numbers (0-9)
- Hyphens (-)
- No spaces, underscores, or special characters

**Valid names:**
- ✅ `hello-lambda-gateway`
- ✅ `DefaultTool`
- ✅ `lambda-target-1`

**Invalid names:**
- ❌ `hello_lambda_gateway` (underscore)
- ❌ `Default Tool` (space)
- ❌ `lambda.target` (period)

### Error: "4 validation errors detected"
**Cause**: Multiple fields are missing or malformed

**Fix**: Use the exact JSON structure provided above

---

## Minimal Valid Lambda Tool Schema

This is the absolute minimum required:

```json
{
  "name": "DefaultTool",
  "description": "Returns greeting message",
  "inputSchema": {
    "json": {
      "type": "object",
      "properties": {}
    }
  }
}
```

**All three fields are REQUIRED and must be non-null.**

---

## Testing Your Configuration

### Test Lambda Target
```bash
aws bedrock-agentcore invoke-gateway \
  --gateway-identifier "arn:aws:bedrock-agentcore:us-east-1:662403250828:gateway/hello-lambda-gateway" \
  --target-name "lambda-target-1" \
  --tool-name "DefaultTool" \
  --tool-input '{}' \
  --region us-east-1
```

### Test MCP Target
```bash
aws bedrock-agentcore invoke-gateway \
  --gateway-identifier "arn:aws:bedrock-agentcore:us-east-1:662403250828:gateway/hello-lambda-gateway" \
  --target-name "mcp-target-1" \
  --tool-name "list_memories" \
  --tool-input '{"limit": 10}' \
  --region us-east-1
```

---

## Configuration Files Reference

Use these files for your setup:

1. **gateway_target_config_lambda.json** - Lambda target only
2. **gateway_target_config_mcp.json** - MCP target only
3. **gateway_complete_config.json** - Both targets together

---

## Checklist Before Saving

- [ ] Gateway name uses only alphanumeric and hyphens
- [ ] Tool name is provided and non-null
- [ ] Tool description is provided and non-null
- [ ] Input schema is provided with valid JSON
- [ ] Lambda ARN is correct and accessible
- [ ] MCP Server ARN is correct and deployed
- [ ] Resource-based policies are applied
- [ ] IAM execution role has permissions

---

## Quick Fix: Copy-Paste Ready Configuration

For AWS Console JSON editor, use this:

**Lambda Target:**
```json
{
  "lambda": {
    "lambdaArn": "arn:aws:lambda:us-east-1:662403250828:function:hello_lambda_tool",
    "toolSchema": {
      "inlinePayload": [
        {
          "name": "DefaultTool",
          "description": "Default tool that returns a greeting message from Lambda",
          "inputSchema": {
            "json": {
              "type": "object",
              "properties": {}
            }
          }
        }
      ]
    }
  }
}
```

**MCP Target:**
```json
{
  "mcp": {
    "mcpServerArn": "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD"
  }
}
```
