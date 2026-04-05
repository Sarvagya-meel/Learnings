# Suggested Changes for MCP Server File

## File: `Agents/agentcore-qna-specialist-agent/03_agentcore_mcp_memory.py`

Your current MCP server implementation is already well-structured! Here are some optional improvements:

## Current Implementation Analysis

### ✅ What's Working Well

1. **JSON-RPC Communication**: Properly implemented with SigV4 auth
2. **Error Handling**: Good try-catch blocks with logging
3. **SSE Response Parsing**: Correctly handles Server-Sent Events format
4. **Memory Integration**: Clean integration with AgentCore Memory
5. **Actor/Session Support**: Multi-user support is implemented
6. **Async Operations**: Uses async/await properly

### 🔧 Suggested Improvements

## 1. Replace Direct Client with Gateway (Optional but Recommended)

### Current Code:
```python
class MCPMemoryClient:
    """Client for interacting with MCP Memory Server via JSON-RPC"""
    # ... 150+ lines of code
```

### Suggested Change:
```python
# Import the gateway
from Scripts.AgentCoreGateway.agentcore_gateway import AgentCoreGateway

# Initialize gateway (singleton pattern)
_gateway = None

def get_mcp_gateway():
    global _gateway
    if _gateway is None:
        _gateway = AgentCoreGateway(
            region=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        _gateway.register_server(
            name="memory",
            arn=MCP_MEMORY_SERVER_ARN,
            description="Memory MCP Server"
        )
    return _gateway
```

### Benefits:
- Reduces code duplication
- Centralized server management
- Easier to add more MCP servers later
- Consistent error handling
- Better testability

## 2. Add Retry Logic

### Add this helper function:
```python
import time
from typing import Callable, TypeVar

T = TypeVar('T')

def retry_with_backoff(
    func: Callable[[], T],
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0
) -> T:
    """Retry a function with exponential backoff"""
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            last_exception = e
            
            if attempt == max_attempts - 1:
                logger.error(f"All {max_attempts} attempts failed: {e}")
                raise
            
            logger.warning(
                f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                f"Retrying in {delay}s..."
            )
            time.sleep(delay)
            delay *= backoff_factor
    
    raise last_exception
```

### Use in retrieve_memory:
```python
async def retrieve_memory(
    query: str,
    actor_id: str,
    session_id: str,
    max_results: int = 5
) -> List[Dict[str, Any]]:
    """Retrieve memories from MCP server with retry logic"""
    try:
        logger.info(f"Retrieving memory for actor={actor_id}, session={session_id}")
        
        gateway = get_mcp_gateway()
        
        # Wrap the call with retry logic
        result = retry_with_backoff(
            lambda: gateway.invoke_mcp_tool(
                server_name="memory",
                tool_name="retrieve_memory",
                arguments={
                    "query": query,
                    "max_results": max_results,
                    "actor_id": actor_id,
                    "session_id": session_id
                }
            ),
            max_attempts=3
        )
        
        # Parse response...
        
    except Exception as e:
        logger.error(f"Memory retrieval failed: {e}", exc_info=True)
        return []  # Graceful degradation
```

## 3. Add Graceful Degradation

### Modify process_query_with_memory:
```python
async def process_query_with_memory(
    query: str,
    actor_id: str,
    session_id: str,
    enable_memory: bool = True  # Add flag to disable memory
) -> Dict[str, Any]:
    """Process a query with optional memory support"""
    
    memories = []
    memory_error = None
    
    # Step 1: Try to retrieve memory (with fallback)
    if enable_memory:
        try:
            memories = await mcp_client.retrieve_memory(
                query=query,
                actor_id=actor_id,
                session_id=session_id,
                max_results=5
            )
        except Exception as e:
            logger.error(f"Memory retrieval failed: {e}")
            memory_error = str(e)
            # Continue without memory instead of failing
    
    # Step 2: Format memory context
    memory_context = format_memory_context(memories)
    
    # Step 3: Build prompt (works with or without memory)
    if memory_context:
        full_prompt = f"{memory_context}\n\nCurrent question: {query}"
        logger.info("Using memory context in query")
    else:
        full_prompt = query
        logger.info("Processing without memory context")
    
    # Step 4: Invoke agent (always works)
    result = agent.invoke({"messages": [("human", full_prompt)]})
    messages = result.get("messages", [])
    answer = messages[-1].content if messages else "No response generated"
    
    # Step 5: Try to store (best effort, don't fail if it doesn't work)
    store_success = False
    if enable_memory:
        try:
            store_success = await mcp_client.store_interaction(
                user_msg=query,
                assistant_msg=answer,
                actor_id=actor_id,
                session_id=session_id
            )
        except Exception as e:
            logger.error(f"Memory storage failed: {e}")
            # Don't fail the request if storage fails
    
    return {
        "result": answer,
        "actor_id": actor_id,
        "session_id": session_id,
        "memory_used": len(memories) > 0,
        "memory_stored": store_success,
        "memory_error": memory_error  # Include error info
    }
```

## 4. Add Memory Context Filtering

### Improve format_memory_context:
```python
def format_memory_context(
    memories: List[Dict[str, Any]],
    min_relevance: float = 0.5  # Add relevance threshold
) -> str:
    """Format retrieved memories with relevance filtering"""
    if not memories:
        return ""
    
    # Filter by relevance score
    relevant = [
        m for m in memories 
        if m.get("relevance", 0.0) >= min_relevance
    ]
    
    if not relevant:
        logger.info(f"No memories above relevance threshold {min_relevance}")
        return ""
    
    lines = ["Previous conversation context (sorted by relevance):"]
    
    for i, mem in enumerate(relevant, 1):
        content = mem.get("content", "")
        strategy = mem.get("strategy", "")
        relevance = mem.get("relevance", 0.0)
        
        if content:
            lines.append(
                f"{i}. [{strategy}] {content} "
                f"(relevance: {relevance:.2f})"
            )
    
    return "\n".join(lines)
```

## 5. Add Connection Pooling

### Use singleton pattern for client:
```python
# At module level
_mcp_client_instance = None

def get_mcp_client() -> MCPMemoryClient:
    """Get or create MCP client instance (singleton)"""
    global _mcp_client_instance
    
    if _mcp_client_instance is None:
        _mcp_client_instance = MCPMemoryClient(
            MCP_MEMORY_SERVER_ARN, 
            AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        logger.info("MCP client initialized")
    
    return _mcp_client_instance

# Then use it:
mcp_client = get_mcp_client()
```

## 6. Add Metrics Tracking

### Add metrics class:
```python
from dataclasses import dataclass
import time

@dataclass
class AgentMetrics:
    """Track agent performance metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency: float = 0.0
    memory_hits: int = 0
    memory_misses: int = 0
    
    def record_request(self, success: bool, latency: float, memory_used: bool):
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        self.total_latency += latency
        
        if memory_used:
            self.memory_hits += 1
        else:
            self.memory_misses += 1
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "success_rate": self.successful_requests / max(self.total_requests, 1),
            "avg_latency_seconds": self.total_latency / max(self.total_requests, 1),
            "memory_hit_rate": self.memory_hits / max(self.total_requests, 1)
        }

# Initialize metrics
metrics = AgentMetrics()

# Use in agent_invocation:
@app.entrypoint
async def agent_invocation(payload, context):
    start_time = time.time()
    success = False
    memory_used = False
    
    try:
        # ... your existing code ...
        response = await process_query_with_memory(query, actor_id, session_id)
        
        success = True
        memory_used = response.get("memory_used", False)
        
        return response
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return {"result": "Error", "error": str(e)}
    
    finally:
        latency = time.time() - start_time
        metrics.record_request(success, latency, memory_used)
        
        # Log metrics periodically
        if metrics.total_requests % 100 == 0:
            logger.info(f"Metrics: {metrics.get_stats()}")
```

## 7. Add Input Validation

### Add validation helper:
```python
def validate_inputs(
    query: str,
    actor_id: str,
    session_id: str
) -> tuple[bool, str]:
    """Validate input parameters"""
    
    if not query or not isinstance(query, str):
        return False, "Query must be a non-empty string"
    
    if len(query) > 10000:
        return False, "Query too long (max 10000 characters)"
    
    if not actor_id or not isinstance(actor_id, str):
        return False, "Actor ID must be a non-empty string"
    
    if len(actor_id) > 256:
        return False, "Actor ID too long (max 256 characters)"
    
    if not session_id or not isinstance(session_id, str):
        return False, "Session ID must be a non-empty string"
    
    if len(session_id) > 256:
        return False, "Session ID too long (max 256 characters)"
    
    return True, ""

# Use in agent_invocation:
@app.entrypoint
async def agent_invocation(payload, context):
    query = payload.get("prompt", payload.get("query", ""))
    actor_id = payload.get("actor_id", DEFAULT_ACTOR_ID)
    session_id = payload.get("session_id", DEFAULT_SESSION_ID)
    
    # Validate inputs
    valid, error_msg = validate_inputs(query, actor_id, session_id)
    if not valid:
        return {
            "result": "Invalid input",
            "error": error_msg,
            "actor_id": actor_id,
            "session_id": session_id
        }
    
    # Continue with processing...
```

## Summary of Changes

### Priority 1 (High Impact):
1. ✅ Add retry logic with exponential backoff
2. ✅ Add graceful degradation for memory failures
3. ✅ Add input validation

### Priority 2 (Medium Impact):
4. ✅ Use gateway instead of direct client (optional)
5. ✅ Add memory context filtering by relevance
6. ✅ Add connection pooling (singleton pattern)

### Priority 3 (Nice to Have):
7. ✅ Add metrics tracking
8. ✅ Add health check endpoint
9. ✅ Add caching for frequently accessed data

## Implementation Steps

1. **Test Current Implementation**: Ensure everything works before making changes
2. **Add Retry Logic**: Start with this as it's low-risk, high-value
3. **Add Graceful Degradation**: Make the agent resilient to memory failures
4. **Add Input Validation**: Prevent invalid requests
5. **Consider Gateway**: If you plan to add more MCP servers, use the gateway
6. **Add Metrics**: Track performance over time
7. **Test Thoroughly**: Test each change independently

## Testing

After making changes, test with:

```bash
# Test the agent
cd Agents/agentcore-qna-specialist-agent
python test_mcp_integration.py

# Or use the gateway test
cd ../../Scripts/AgentCoreGateway
python test_gateway.py
```

## Notes

- Your current implementation is solid and production-ready
- These are enhancements, not fixes
- Implement changes incrementally
- Test after each change
- Monitor CloudWatch logs for any issues
