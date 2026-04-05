"""
Example: MCP Memory Server with Agent Caller

This shows how to integrate the agent caller into your MCP server
so the MCP server can invoke the QNA agent.

Use case: Memory server receives a query, calls QNA agent to answer,
then stores the interaction in memory.
"""

import os
import logging
from typing import Optional

from mcp.server.fastmcp import FastMCP
from mcp_node_caller import AgentCoreCaller

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("mcp.server.with.agent")

# Configuration
QNA_AGENT_ARN = os.getenv(
    "QNA_AGENT_ARN",
    "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_qna_agent-LuJi165oYZ"
)
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# Initialize MCP server
mcp = FastMCP("memory_with_agent", host="0.0.0.0", stateless_http=True)

# Initialize agent caller
agent_caller = AgentCoreCaller(
    agent_arn=QNA_AGENT_ARN,
    region=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)


@mcp.tool()
def ask_agent(
    query: str,
    actor_id: str = "default-user",
    session_id: Optional[str] = None,
    enable_memory: bool = True
) -> dict:
    """
    Ask the QNA agent a question
    
    This tool allows the MCP server to invoke the QNA agent.
    The agent will use its FAQ knowledge base and memory to answer.
    
    Args:
        query: The question to ask
        actor_id: Actor identifier (for memory)
        session_id: Session identifier (for memory)
        enable_memory: Whether agent should use memory
        
    Returns:
        Agent response with answer and metadata
    """
    logger.info(f"Asking agent: {query[:50]}...")
    
    try:
        result = agent_caller.invoke_agent(
            prompt=query,
            actor_id=actor_id,
            session_id=session_id,
            enable_memory=enable_memory
        )
        
        logger.info("Agent responded successfully")
        
        return {
            "success": True,
            "answer": result.get("result", "No answer"),
            "metadata": {
                "actor_id": result.get("actor_id"),
                "session_id": result.get("session_id"),
                "memory_used": result.get("memory_used", False),
                "memory_stored": result.get("memory_stored", False),
                "processing_time": result.get("processing_time_seconds")
            }
        }
        
    except Exception as e:
        logger.error(f"Agent call failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


@mcp.tool()
def ask_agent_simple(query: str) -> str:
    """
    Simple version - just returns the answer text
    
    Args:
        query: The question to ask
        
    Returns:
        Answer text
    """
    logger.info(f"Simple ask: {query[:50]}...")
    
    try:
        answer = agent_caller.invoke_agent_simple(query)
        return answer
    except Exception as e:
        logger.error(f"Agent call failed: {e}")
        return f"Error: {e}"


@mcp.tool()
def ask_and_remember(
    query: str,
    actor_id: str,
    session_id: str
) -> dict:
    """
    Ask agent and ensure the interaction is stored in memory
    
    This is a convenience tool that:
    1. Calls the QNA agent with the query
    2. Ensures memory is enabled
    3. Returns both answer and memory status
    
    Args:
        query: The question to ask
        actor_id: Actor identifier
        session_id: Session identifier
        
    Returns:
        Response with answer and memory confirmation
    """
    logger.info(f"Ask and remember: {query[:50]}...")
    
    try:
        result = agent_caller.invoke_agent(
            prompt=query,
            actor_id=actor_id,
            session_id=session_id,
            enable_memory=True
        )
        
        answer = result.get("result", "No answer")
        memory_stored = result.get("memory_stored", False)
        
        if not memory_stored:
            logger.warning("Memory storage failed or disabled")
        
        return {
            "success": True,
            "answer": answer,
            "memory_stored": memory_stored,
            "actor_id": actor_id,
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Ask and remember failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def batch_ask(
    queries: list[str],
    actor_id: str = "batch-user",
    session_id: Optional[str] = None
) -> dict:
    """
    Ask multiple questions in batch
    
    Args:
        queries: List of questions to ask
        actor_id: Actor identifier
        session_id: Session identifier
        
    Returns:
        Results for all queries
    """
    logger.info(f"Batch ask: {len(queries)} queries")
    
    results = []
    
    for i, query in enumerate(queries, 1):
        logger.info(f"Processing query {i}/{len(queries)}")
        
        try:
            result = agent_caller.invoke_agent(
                prompt=query,
                actor_id=actor_id,
                session_id=session_id
            )
            
            results.append({
                "query": query,
                "success": True,
                "answer": result.get("result", "No answer")
            })
            
        except Exception as e:
            logger.error(f"Query {i} failed: {e}")
            results.append({
                "query": query,
                "success": False,
                "error": str(e)
            })
    
    successful = sum(1 for r in results if r.get("success"))
    
    return {
        "total": len(queries),
        "successful": successful,
        "failed": len(queries) - successful,
        "results": results
    }


@mcp.tool()
def agent_health_check() -> dict:
    """
    Check if the QNA agent is reachable and responding
    
    Returns:
        Health status
    """
    logger.info("Checking agent health...")
    
    try:
        # Try a simple query
        result = agent_caller.invoke_agent(
            prompt="health check",
            enable_memory=False,
            timeout=10.0
        )
        
        return {
            "healthy": True,
            "agent_arn": QNA_AGENT_ARN,
            "region": AWS_REGION,
            "response_received": True
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "healthy": False,
            "agent_arn": QNA_AGENT_ARN,
            "region": AWS_REGION,
            "error": str(e)
        }


if __name__ == "__main__":
    logger.info("Starting MCP server with agent caller...")
    logger.info(f"Agent ARN: {QNA_AGENT_ARN}")
    
    # Run the MCP server
    mcp.run(transport="streamable-http")
