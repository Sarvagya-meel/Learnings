# Gateway Target Architecture Diagram

## Current Setup: Adding MCP Server as Gateway Target

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AWS Account 662403250828                     │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    AgentCore Gateway                           │ │
│  │                                                                │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │                    Gateway Targets                        │ │ │
│  │  │                                                           │ │ │
│  │  │  ┌─────────────────────────────────────────────────┐    │ │ │
│  │  │  │  Target: memory-mcp-server                      │    │ │ │
│  │  │  │  Type: MCP_SERVER                               │    │ │ │
│  │  │  │  Protocol: MCP (2025-06-18)                     │    │ │ │
│  │  │  │  Auth: AWS_SIGV4                                │    │ │ │
│  │  │  │                                                  │    │ │ │
│  │  │  │  Tools:                                          │    │ │ │
│  │  │  │  • retrieve_memory                               │    │ │ │
│  │  │  │  • store_interaction                             │    │ │ │
│  │  │  │  • server_info                                   │    │ │ │
│  │  │  └─────────────────────────────────────────────────┘    │ │ │
│  │  │                                                           │ │ │
│  │  │  [Future: Add more targets here]                         │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  │                                                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│                              │                                       │
│                              │ HTTPS + AWS SigV4                     │
│                              │                                       │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              MCP Memory Server Runtime                         │ │
│  │                                                                │ │
│  │  ARN: arn:aws:bedrock-agentcore:us-east-1:662403250828:      │ │
│  │       runtime/agentcore_memory_mcp_server-R4jmV6ERZD         │ │
│  │                                                                │ │
│  │  Endpoint:                                                     │ │
│  │  https://bedrock-agentcore.us-east-1.amazonaws.com/          │ │
│  │  runtimes/.../runtime-endpoint/DEFAULT/invocations           │ │
│  │                                                                │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │  FastMCP Server (Python 3.13)                           │ │ │
│  │  │                                                          │ │ │
│  │  │  Tools Implementation:                                   │ │ │
│  │  │  ┌────────────────────────────────────────────────────┐ │ │ │
│  │  │  │  @mcp.tool()                                       │ │ │ │
│  │  │  │  def retrieve_memory(query, actor_id, ...)        │ │ │ │
│  │  │  │      → Query AgentCore Memory                      │ │ │ │
│  │  │  │      → Return relevant memories                    │ │ │ │
│  │  │  └────────────────────────────────────────────────────┘ │ │ │
│  │  │  ┌────────────────────────────────────────────────────┐ │ │ │
│  │  │  │  @mcp.tool()                                       │ │ │ │
│  │  │  │  def store_interaction(user_msg, assistant_msg)   │ │ │ │
│  │  │  │      → Store in AgentCore Memory                   │ │ │ │
│  │  │  │      → Return success status                       │ │ │ │
│  │  │  └────────────────────────────────────────────────────┘ │ │ │
│  │  │  ┌────────────────────────────────────────────────────┐ │ │ │
│  │  │  │  @mcp.tool()                                       │ │ │ │
│  │  │  │  def server_info(session_id)                       │ │ │ │
│  │  │  │      → Return server health/status                 │ │ │ │
│  │  │  └────────────────────────────────────────────────────┘ │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  │                                                                │ │
│  │                              │                                 │ │
│  │                              │                                 │ │
│  │                              ▼                                 │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │         AgentCore Memory Service                         │ │ │
│  │  │                                                          │ │ │
│  │  │  Memory ID: MyAgentMemory20260211160131-gMGdB67nD0     │ │ │
│  │  │                                                          │ │ │
│  │  │  Stores:                                                 │ │ │
│  │  │  • User messages                                         │ │ │
│  │  │  • Assistant responses                                   │ │ │
│  │  │  • Actor/Session context                                │ │ │
│  │  │  • Semantic embeddings                                   │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Request Flow

### 1. Agent Invokes Tool via Gateway

```
Agent
  │
  │ invoke_tool("retrieve_memory", {query: "...", actor_id: "..."})
  │
  ▼
Gateway
  │
  │ Route to target: memory-mcp-server
  │ Add AWS SigV4 authentication
  │
  ▼
MCP Server Runtime
  │
  │ JSON-RPC: {"method": "tools/call", "params": {...}}
  │
  ▼
FastMCP Server
  │
  │ Execute: retrieve_memory(query, actor_id, ...)
  │
  ▼
AgentCore Memory
  │
  │ Semantic search
  │ Return relevant memories
  │
  ▼
FastMCP Server
  │
  │ Format response
  │
  ▼
MCP Server Runtime
  │
  │ JSON-RPC response
  │
  ▼
Gateway
  │
  │ Parse and forward
  │
  ▼
Agent
  │
  │ Use memories in context
  └─
```

## Configuration Flow

### Step-by-Step Setup

```
1. Deploy MCP Server
   ├─ Code: memory_mcp_server.py
   ├─ Deploy: bedrock-agentcore deploy
   └─ Result: Runtime ARN created

2. Apply Resource Policy
   ├─ Script: apply_gateway_policy.py
   ├─ Policy: Allow gateway to invoke
   └─ Result: Gateway can access server

3. Add Target to Gateway
   ├─ Target Name: memory-mcp-server
   ├─ Endpoint: Runtime invocation URL
   ├─ Protocol: MCP (2025-06-18)
   └─ Result: Target registered

4. Test Connection
   ├─ Script: test_gateway.py
   ├─ Test: List tools, invoke tools
   └─ Result: All tests pass ✓

5. Use in Agent
   ├─ Code: AgentCoreCaller or Gateway
   ├─ Invoke: retrieve_memory, store_interaction
   └─ Result: Agent has memory! 🎉
```

## Authentication Flow

```
┌─────────────┐
│   Gateway   │
└──────┬──────┘
       │
       │ 1. Build request
       │    Method: POST
       │    Body: JSON-RPC payload
       │
       ▼
┌─────────────────────┐
│  AWS SigV4 Signing  │
│                     │
│  Service: bedrock-  │
│           agentcore │
│  Region: us-east-1  │
└──────┬──────────────┘
       │
       │ 2. Add headers:
       │    Authorization: AWS4-HMAC-SHA256 ...
       │    X-Amz-Date: ...
       │    X-Amz-Security-Token: ...
       │
       ▼
┌─────────────────────┐
│  HTTPS Request      │
│                     │
│  To: bedrock-       │
│      agentcore      │
│      endpoint       │
└──────┬──────────────┘
       │
       │ 3. Verify signature
       │    Check resource policy
       │
       ▼
┌─────────────────────┐
│  MCP Server         │
│  Runtime            │
│                     │
│  ✓ Authorized       │
│  ✓ Execute request  │
└─────────────────────┘
```

## Data Flow: Store & Retrieve

```
User Query
    │
    ▼
┌─────────────────────────────────────────┐
│  Agent: process_query_with_memory()     │
│                                         │
│  1. Retrieve Context                    │
│     ├─ Gateway.invoke_tool()            │
│     │  └─ retrieve_memory(query)        │
│     │     └─ MCP Server                 │
│     │        └─ AgentCore Memory        │
│     │           └─ Return: [memories]   │
│     │                                    │
│  2. Build Prompt                        │
│     ├─ Format memories                  │
│     └─ Add current query                │
│                                         │
│  3. Generate Response                   │
│     └─ LLM with context                 │
│                                         │
│  4. Store Interaction                   │
│     ├─ Gateway.invoke_tool()            │
│     │  └─ store_interaction()           │
│     │     └─ MCP Server                 │
│     │        └─ AgentCore Memory        │
│     │           └─ Stored ✓             │
│     │                                    │
│  5. Return Response                     │
│     └─ Answer with metadata             │
└─────────────────────────────────────────┘
    │
    ▼
Response to User
```

## Key Components

### 1. Gateway Target
- **Name:** memory-mcp-server
- **Type:** MCP_SERVER
- **Status:** ACTIVE
- **Tools:** 3 (retrieve, store, info)

### 2. MCP Server Runtime
- **ARN:** ...R4jmV6ERZD
- **Protocol:** MCP
- **Runtime:** Python 3.13
- **Network:** PUBLIC

### 3. FastMCP Server
- **Framework:** FastMCP
- **Transport:** streamable-http
- **Stateless:** True
- **Tools:** 3 implemented

### 4. AgentCore Memory
- **Memory ID:** ...gMGdB67nD0
- **Type:** STM_AND_LTM
- **Storage:** Semantic search
- **Expiry:** 30 days

## Security Layers

```
┌─────────────────────────────────────────┐
│  Layer 1: IAM Permissions               │
│  ├─ User/Role must have:                │
│  │  • bedrock-agentcore:InvokeRuntime   │
│  │  • bedrock-agentcore:InvokeGateway   │
│  └─ Verified at: API Gateway            │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  Layer 2: Resource Policy               │
│  ├─ MCP Server must allow:              │
│  │  • Service: bedrock-agentcore        │
│  │  • Account: 662403250828             │
│  └─ Verified at: Runtime invocation     │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  Layer 3: AWS SigV4 Authentication      │
│  ├─ Request must be signed              │
│  │  • Signature valid                   │
│  │  • Timestamp fresh                   │
│  └─ Verified at: AWS API                │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  Layer 4: Network Security              │
│  ├─ HTTPS only                          │
│  │  • TLS 1.2+                          │
│  │  • Certificate validation            │
│  └─ Verified at: Transport layer        │
└─────────────────────────────────────────┘
```

## Summary

Your MCP memory server is now integrated as a gateway target, enabling:

✅ **Centralized Access** - All agents use gateway to access memory
✅ **Secure Communication** - AWS SigV4 + Resource policies
✅ **Tool Discovery** - Gateway knows available tools
✅ **Automatic Routing** - Gateway routes to correct server
✅ **Error Handling** - Gateway handles retries and errors
✅ **Monitoring** - CloudWatch logs all interactions

Next: Use the gateway in your agents to leverage memory capabilities!
