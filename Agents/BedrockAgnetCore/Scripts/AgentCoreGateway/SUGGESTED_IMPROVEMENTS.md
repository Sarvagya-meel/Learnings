# Suggested Improvements for MCP Server and Agent Integration

## MCP Server Improvements (`memory_mcp_server.py`)

### 1. Add Health Check Endpoint
The server already has `server_info` tool which is good. Consider adding:

```python
@mcp.tool()
def health_check() -> ToolResponse:
    """Quick health check without heavy operations"""
    return ToolResponse.ok(
        "health_check",
        "Server is healthy",
        data={"status": "healthy", "timestamp": time.time()},
        status=200
    )
```

### 2. Add Request Tracing
Already implemented with `session_id` - good! Consider adding:

```python
# Add correlation ID to all log messages
logger = logging.LoggerAdapter(logger, {"session_id": session_id})
```

### 3. Improve Error Messages
Current error handling is good. Consider adding error codes:

```python
ERROR_CODES = {
    "VALIDATION_ERROR": 400,
    "NOT_FOUND": 404,
    "STORE_FAILED": 502,
    "INTERNAL": 500,
    "TIMEOUT": 504
}
```

### 4. Add Rate Limiting (Optional)
For production, consider adding rate limiting per actor:

```python
from collections import defaultdict
import time

class RateLimiter:
    def __init__(self, max_requests=100, window=60):
        self.max_requests = max_requests
        self.window = window
        self.requests = defaultdict(list)
    
    def check(self, actor_id: str) -> bool:
        now = time.time()
        # Clean old requests
        self.requests[actor_id] = [
            t for t in self.requests[actor_id] 
            if now - t < self.window
        ]
        # Check limit
        if len(self.requests[actor_id]) >= self.max_requests:
            return False
        self.requests[actor_id].append(now)
        return True
```

### 5. Add Batch Operations
For efficiency, add batch retrieve/store:

```python
@mcp.tool()
def retrieve_memory_batch(
    queries: List[str],
    max_results_per_query: int = 5,
    actor_id: str = ACTOR_ID_ENV,
    session_id: Optional[str] = None
) -> ToolResponse:
    """Retrieve memories for multiple queries at once"""
    # Implementation
    pass
```

## Agent File Improvements (`03_agentcore_mcp_memory.py`)

### 1. Use Gateway Instead of Direct Client ✅ RECOMMENDED

Replace the `MCPMemoryClient` class with the gateway:

```python
from Scripts.AgentCoreGateway.agentcore_gateway import AgentCoreGateway

# Initialize gateway instead of client
gateway = AgentCoreGateway(
    region=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

gateway.register_server(
    name="memory",
    arn=MCP_MEMORY_SERVER_ARN,
    description="Memory MCP Server"
)

# Then use gateway methods
async def retrieve_memory(query, actor_id, session_id, max_results=5):
    result = gateway.invoke_mcp_tool(
        server_name="memory",
        tool_name="retrieve_memory",
        arguments={
            "query": query,
            "max_results": max_results,
            "actor_id": actor_id,
            "session_id": session_id
        }
    )
    # Parse result...
```

### 2. Add Connection Pooling

```python
from functools import lru_cache

@lru_cache(maxsize=1)
def get_gateway():
    """Singleton gateway instance"""
    gateway = AgentCoreGateway(...)
    gateway.register_server(...)
    return gateway
```

### 3. Add Retry Logic with Exponential Backoff

```python
import time
from typing import Callable, Any

def retry_with_backoff(
    func: Callable,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0
) -> Any:
    """Retry a function with exponential backoff"""
    delay = initial_delay
    
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            
            logger.warning(
                f"Attempt {attempt + 1} failed: {e}. "
                f"Retrying in {delay}s..."
            )
            time.sleep(delay)
            delay *= backoff_factor
```

Usage:
```python
result = retry_with_backoff(
    lambda: gateway.invoke_mcp_tool(...)
)
```

### 4. Add Caching for Frequently Accessed Memories

```python
from functools import lru_cache
import hashlib

def cache_key(query: str, actor_id: str, session_id: str) -> str:
    """Generate cache key"""
    data = f"{query}:{actor_id}:{session_id}"
    return hashlib.md5(data.encode()).hexdigest()

# Simple in-memory cache with TTL
from datetime import datetime, timedelta

class MemoryCache:
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl = timedelta(seconds=ttl_seconds)
    
    def get(self, key: str):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                return value
            del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        self.cache[key] = (value, datetime.now())

memory_cache = MemoryCache(ttl_seconds=300)  # 5 min cache
```

### 5. Add Async Support Throughout

The agent already uses `async` for the main functions, but ensure all I/O is async:

```python
import asyncio
import aiohttp

class AsyncAgentCoreGateway:
    """Async version of the gateway"""
    
    async def invoke_mcp_tool_async(self, ...):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=body) as response:
                return await response.json()
```

### 6. Add Metrics and Monitoring

```python
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class Metrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency: float = 0.0
    memory_hits: int = 0
    memory_misses: int = 0
    
    def record_request(self, success: bool, latency: float):
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        self.total_latency += latency
    
    def to_dict(self):
        return {
            "total_requests": self.total_requests,
            "success_rate": self.successful_requests / max(self.total_requests, 1),
            "avg_latency": self.total_latency / max(self.total_requests, 1),
            "memory_hit_rate": self.memory_hits / max(self.memory_hits + self.memory_misses, 1)
        }

metrics = Metrics()

# Use in code
import time
start = time.time()
try:
    result = gateway.invoke_mcp_tool(...)
    metrics.record_request(True, time.time() - start)
except Exception:
    metrics.record_request(False, time.time() - start)
    raise
```

### 7. Improve Memory Context Formatting

Current implementation is good. Consider adding relevance threshold:

```python
def format_memory_context(
    memories: List[Dict[str, Any]], 
    min_relevance: float = 0.5
) -> str:
    """Format memories with relevance filtering"""
    if not memories:
        return ""
    
    # Filter by relevance
    relevant = [m for m in memories if m.get("relevance", 0) >= min_relevance]
    
    if not relevant:
        return ""
    
    lines = ["Previous conversation context (sorted by relevance):"]
    for i, mem in enumerate(relevant, 1):
        content = mem.get("content", "")
        relevance = mem.get("relevance", 0.0)
        strategy = mem.get("strategy", "")
        
        lines.append(
            f"{i}. [{strategy}] {content} "
            f"(relevance: {relevance:.2f})"
        )
    
    return "\n".join(lines)
```

### 8. Add Graceful Degradation

If memory service is down, agent should still work:

```python
async def process_query_with_memory(
    query: str,
    actor_id: str,
    session_id: str,
    fallback_on_error: bool = True
) -> Dict[str, Any]:
    """Process query with optional fallback"""
    
    memories = []
    memory_error = None
    
    # Try to retrieve memory
    try:
        memories = await retrieve_memory_safe(query, actor_id, session_id)
    except Exception as e:
        logger.error(f"Memory retrieval failed: {e}")
        memory_error = str(e)
        if not fallback_on_error:
            raise
    
    # Continue processing even if memory failed
    memory_context = format_memory_context(memories)
    full_prompt = f"{memory_context}\n\nCurrent question: {query}" if memory_context else query
    
    # Invoke agent
    result = agent.invoke({"messages": [("human", full_prompt)]})
    answer = result.get("messages", [])[-1].content if result.get("messages") else "No response"
    
    # Try to store (best effort)
    store_success = False
    try:
        store_success = await store_interaction_safe(
            user_msg=query,
            assistant_msg=answer,
            actor_id=actor_id,
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Memory storage failed: {e}")
    
    return {
        "result": answer,
        "actor_id": actor_id,
        "session_id": session_id,
        "memory_used": len(memories) > 0,
        "memory_stored": store_success,
        "memory_error": memory_error
    }
```

## Deployment Improvements

### 1. Add Resource Policy Automation

Create a script that automatically applies policies during deployment:

```python
# In deployment script
from apply_gateway_policy import apply_policy_via_api

def post_deploy_hook():
    """Run after MCP server deployment"""
    print("Applying resource policies...")
    apply_policy_via_api()
    print("Resource policies applied!")
```

### 2. Add Environment-Specific Configs

```yaml
# config/dev.yaml
mcp_servers:
  memory:
    arn: "arn:aws:bedrock-agentcore:us-east-1:ACCOUNT:runtime/memory-dev"
    timeout: 30

# config/prod.yaml
mcp_servers:
  memory:
    arn: "arn:aws:bedrock-agentcore:us-east-1:ACCOUNT:runtime/memory-prod"
    timeout: 60
    retry_attempts: 5
```

### 3. Add Integration Tests

```python
# tests/test_gateway_integration.py
import pytest
from agentcore_gateway import AgentCoreGateway

@pytest.fixture
def gateway():
    gw = AgentCoreGateway()
    gw.register_server("memory", MCP_SERVER_ARN)
    return gw

def test_list_tools(gateway):
    tools = gateway.list_tools("memory")
    assert len(tools) > 0
    assert any(t["name"] == "retrieve_memory" for t in tools)

def test_store_and_retrieve(gateway):
    # Store
    result = gateway.invoke_mcp_tool(
        "memory", "store_interaction",
        {"user_msg": "test", "assistant_msg": "response", ...}
    )
    assert result["data"]["stored"] == True
    
    # Retrieve
    result = gateway.invoke_mcp_tool(
        "memory", "retrieve_memory",
        {"query": "test", ...}
    )
    assert len(result["data"]["items"]) > 0
```

## Security Improvements

### 1. Add Input Validation

```python
def validate_actor_id(actor_id: str) -> bool:
    """Validate actor ID format"""
    if not actor_id or len(actor_id) > 256:
        return False
    # Add more validation
    return True
```

### 2. Add Request Signing Verification

For production, verify that requests to the gateway are properly signed.

### 3. Add Audit Logging

```python
def audit_log(event: str, actor_id: str, details: Dict[str, Any]):
    """Log security-relevant events"""
    logger.info(
        "AUDIT",
        extra={
            "event": event,
            "actor_id": actor_id,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details
        }
    )
```

## Summary of Priority Changes

### High Priority (Do First):
1. ✅ Use the gateway instead of direct MCP client in agent
2. ✅ Add retry logic with exponential backoff
3. ✅ Add graceful degradation for memory failures
4. ✅ Ensure resource policies are applied

### Medium Priority:
5. Add caching for frequently accessed memories
6. Add metrics and monitoring
7. Add integration tests
8. Improve error messages with error codes

### Low Priority (Nice to Have):
9. Add rate limiting
10. Add batch operations
11. Add health check endpoint
12. Environment-specific configs
