"""
Example: QNA Agent Using AgentCore Gateway

This is a refactored version showing how to use the gateway
instead of direct MCP client implementation.

Key improvements:
1. Uses centralized gateway for all MCP communication
2. Adds retry logic and error handling
3. Implements graceful degradation
4. Adds metrics tracking
"""

import os
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

# Import the gateway
import sys
sys.path.append(os.path.dirname(__file__))
from agentcore_gateway import AgentCoreGateway

from bedrock_agentcore.runtime import BedrockAgentCoreApp

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("qna.specialist.gateway")

# Configuration
MCP_MEMORY_SERVER_ARN = os.getenv(
    "MCP_MEMORY_SERVER_ARN",
    "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD"
)
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
DEFAULT_ACTOR_ID = "qna-specialist-user"
DEFAULT_SESSION_ID = "default-session"

# Create AgentCore app
app = BedrockAgentCoreApp()

# ============================================================================
# Gateway Initialization (Singleton Pattern)
# ============================================================================

_gateway_instance = None

def get_gateway() -> AgentCoreGateway:
    """Get or create gateway instance (singleton)"""
    global _gateway_instance
    
    if _gateway_instance is None:
        logger.info("Initializing AgentCore Gateway...")
        
        _gateway_instance = AgentCoreGateway(
            region=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        # Register MCP servers
        _gateway_instance.register_server(
            name="memory",
            arn=MCP_MEMORY_SERVER_ARN,
            description="AgentCore Memory MCP Server",
            tags=["memory", "storage", "context"]
        )
        
        logger.info("Gateway initialized successfully")
    
    return _gateway_instance


# ============================================================================
# Memory Operations with Retry Logic
# ============================================================================

def retry_with_backoff(func, max_attempts=3, initial_delay=1.0, backoff_factor=2.0):
    """Retry a function with exponential backoff"""
    import time
    
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


async def retrieve_memory_safe(
    query: str,
    actor_id: str,
    session_id: str,
    max_results: int = 5
) -> List[Dict[str, Any]]:
    """
    Safely retrieve memories with retry logic
    
    Returns empty list on failure instead of raising exception
    """
    try:
        gateway = get_gateway()
        
        def _retrieve():
            return gateway.invoke_mcp_tool(
                server_name="memory",
                tool_name="retrieve_memory",
                arguments={
                    "query": query,
                    "max_results": max_results,
                    "actor_id": actor_id,
                    "session_id": session_id
                }
            )
        
        result = retry_with_backoff(_retrieve, max_attempts=3)
        
        # Parse the response
        content = result.get("structuredContent", {}).get("result", {}).get("content", [{}])
        if content:
            import json
            text = content[0].get("text", "{}")
            data = json.loads(text) if isinstance(text, str) else text
            items = data.get("data", {}).get("items", [])
            
            logger.info(f"Retrieved {len(items)} memories for actor={actor_id}")
            return items
        
        return []
        
    except Exception as e:
        logger.error(f"Memory retrieval failed after retries: {e}", exc_info=True)
        return []  # Graceful degradation


async def store_interaction_safe(
    user_msg: str,
    assistant_msg: str,
    actor_id: str,
    session_id: str
) -> bool:
    """
    Safely store interaction with retry logic
    
    Returns False on failure instead of raising exception
    """
    try:
        gateway = get_gateway()
        
        def _store():
            return gateway.invoke_mcp_tool(
                server_name="memory",
                tool_name="store_interaction",
                arguments={
                    "user_msg": user_msg,
                    "assistant_msg": assistant_msg,
                    "actor_id": actor_id,
                    "session_id": session_id
                }
            )
        
        result = retry_with_backoff(_store, max_attempts=3)
        
        # Parse the response
        content = result.get("structuredContent", {}).get("result", {}).get("content", [{}])
        if content:
            import json
            text = content[0].get("text", "{}")
            data = json.loads(text) if isinstance(text, str) else text
            stored = data.get("data", {}).get("stored", False)
            
            if stored:
                logger.info(f"Stored interaction for actor={actor_id}")
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Memory storage failed after retries: {e}", exc_info=True)
        return False  # Graceful degradation


# ============================================================================
# Memory Context Formatting
# ============================================================================

def format_memory_context(
    memories: List[Dict[str, Any]], 
    min_relevance: float = 0.5
) -> str:
    """
    Format retrieved memories into a readable context string
    
    Args:
        memories: List of memory items
        min_relevance: Minimum relevance score to include (0.0 to 1.0)
    
    Returns:
        Formatted context string
    """
    if not memories:
        return ""
    
    # Filter by relevance
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


# ============================================================================
# Main Query Processing
# ============================================================================

async def process_query_with_memory(
    query: str,
    actor_id: str,
    session_id: str,
    agent_invoke_func,  # Your agent's invoke function
    enable_memory: bool = True,
    min_relevance: float = 0.5
) -> Dict[str, Any]:
    """
    Process a query with memory retrieval and storage
    
    Args:
        query: User query
        actor_id: Actor identifier
        session_id: Session identifier
        agent_invoke_func: Function to invoke your agent
        enable_memory: Whether to use memory (for testing/fallback)
        min_relevance: Minimum relevance for memory context
    
    Returns:
        Response dictionary with result and metadata
    """
    import time
    start_time = time.time()
    
    memories = []
    memory_error = None
    
    # Step 1: Retrieve memory context (if enabled)
    if enable_memory:
        try:
            memories = await retrieve_memory_safe(
                query=query,
                actor_id=actor_id,
                session_id=session_id,
                max_results=5
            )
        except Exception as e:
            logger.error(f"Memory retrieval error: {e}")
            memory_error = str(e)
            # Continue without memory (graceful degradation)
    
    # Step 2: Format memory context
    memory_context = format_memory_context(memories, min_relevance=min_relevance)
    
    # Step 3: Build the full prompt
    if memory_context:
        full_prompt = f"{memory_context}\n\nCurrent question: {query}"
        logger.info(f"Using {len(memories)} memories in context")
    else:
        full_prompt = query
        logger.info("No memory context available")
    
    # Step 4: Invoke the agent
    try:
        result = agent_invoke_func({"messages": [("human", full_prompt)]})
        messages = result.get("messages", [])
        answer = messages[-1].content if messages else "No response generated"
    except Exception as e:
        logger.error(f"Agent invocation failed: {e}", exc_info=True)
        answer = "I apologize, but I encountered an error processing your request."
    
    # Step 5: Store the interaction (if enabled and successful)
    store_success = False
    if enable_memory and answer:
        try:
            store_success = await store_interaction_safe(
                user_msg=query,
                assistant_msg=answer,
                actor_id=actor_id,
                session_id=session_id
            )
        except Exception as e:
            logger.error(f"Memory storage error: {e}")
    
    # Calculate metrics
    processing_time = time.time() - start_time
    
    return {
        "result": answer,
        "actor_id": actor_id,
        "session_id": session_id,
        "memory_used": len(memories) > 0,
        "memory_count": len(memories),
        "memory_stored": store_success,
        "memory_error": memory_error,
        "processing_time_seconds": round(processing_time, 3)
    }


# ============================================================================
# AgentCore Entrypoint
# ============================================================================

@app.entrypoint
async def agent_invocation(payload, context):
    """
    Handler for agent invocation in AgentCore runtime
    
    This is the main entry point that AgentCore calls
    """
    logger.info(f"Received invocation: {payload}")
    
    try:
        # Extract parameters
        query = payload.get("prompt", payload.get("query", ""))
        actor_id = payload.get("actor_id", DEFAULT_ACTOR_ID)
        session_id = payload.get("session_id", payload.get("thread_id", DEFAULT_SESSION_ID))
        enable_memory = payload.get("enable_memory", True)
        
        if not query:
            return {
                "result": "No query provided",
                "error": "Missing 'prompt' or 'query' in payload",
                "actor_id": actor_id,
                "session_id": session_id
            }
        
        # Import your agent here (or define it above)
        # For this example, we'll use a placeholder
        def mock_agent_invoke(messages):
            # Replace with your actual agent
            return {
                "messages": [
                    type('Message', (), {'content': f"Mock response to: {messages['messages'][0][1]}"})()
                ]
            }
        
        # Process the query
        response = await process_query_with_memory(
            query=query,
            actor_id=actor_id,
            session_id=session_id,
            agent_invoke_func=mock_agent_invoke,
            enable_memory=enable_memory
        )
        
        logger.info(
            f"Query processed: memory_used={response['memory_used']}, "
            f"memory_stored={response['memory_stored']}, "
            f"time={response['processing_time_seconds']}s"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing invocation: {e}", exc_info=True)
        return {
            "result": "I apologize, but I encountered an error processing your request.",
            "error": str(e),
            "error_type": type(e).__name__,
            "actor_id": payload.get("actor_id", DEFAULT_ACTOR_ID),
            "session_id": payload.get("session_id", DEFAULT_SESSION_ID)
        }


# ============================================================================
# Testing
# ============================================================================

async def test_gateway_integration():
    """Test the gateway integration"""
    print("="*80)
    print("Testing Gateway Integration")
    print("="*80)
    
    # Test 1: List tools
    print("\n1. Listing available tools...")
    try:
        gateway = get_gateway()
        tools = gateway.list_tools("memory")
        print(f"✓ Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.get('name')}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    # Test 2: Store and retrieve
    print("\n2. Testing store and retrieve...")
    try:
        test_actor = "test-user-123"
        test_session = "test-session-456"
        
        # Store
        stored = await store_interaction_safe(
            user_msg="What is AgentCore?",
            assistant_msg="AgentCore is AWS's framework for building AI agents.",
            actor_id=test_actor,
            session_id=test_session
        )
        print(f"✓ Store result: {stored}")
        
        # Retrieve
        memories = await retrieve_memory_safe(
            query="AgentCore",
            actor_id=test_actor,
            session_id=test_session,
            max_results=3
        )
        print(f"✓ Retrieved {len(memories)} memories")
        
        # Format
        context = format_memory_context(memories)
        print(f"✓ Formatted context:\n{context}")
        
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    print("\n" + "="*80)
    print("Tests completed!")
    print("="*80)


if __name__ == "__main__":
    import asyncio
    
    # Run tests
    asyncio.run(test_gateway_integration())
    
    # Or run the app
    # app.run()
