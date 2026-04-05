"""
Test script for QNA Specialist Agent with MCP Memory Integration

This script helps you test the agent locally before deployment.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import the agent
from importlib import import_module

# Dynamically import the agent module
agent_module = import_module("03_agentcore_mcp_memory")


async def test_single_query():
    """Test a single query without memory context"""
    print("\n" + "="*80)
    print("TEST 1: Single Query (No Memory Context)")
    print("="*80)
    
    payload = {
        "prompt": "What is roaming activation?",
        "actor_id": "test-user-001",
        "session_id": "test-session-001"
    }
    
    print(f"\nQuery: {payload['prompt']}")
    print(f"Actor ID: {payload['actor_id']}")
    print(f"Session ID: {payload['session_id']}")
    
    result = await agent_module.agent_invocation(payload, {})
    
    print(f"\nResponse: {result['result']}")
    print(f"Memory Used: {result.get('memory_used', False)}")
    print(f"Memory Stored: {result.get('memory_stored', False)}")


async def test_multi_turn_conversation():
    """Test a multi-turn conversation with memory context"""
    print("\n" + "="*80)
    print("TEST 2: Multi-Turn Conversation (With Memory Context)")
    print("="*80)
    
    actor_id = "test-user-002"
    session_id = "test-session-002"
    
    queries = [
        "What are the roaming charges?",
        "How do I activate it?",
        "Can I use it internationally?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n--- Turn {i} ---")
        print(f"Query: {query}")
        
        payload = {
            "prompt": query,
            "actor_id": actor_id,
            "session_id": session_id
        }
        
        result = await agent_module.agent_invocation(payload, {})
        
        print(f"Response: {result['result'][:200]}...")  # Truncate for readability
        print(f"Memory Used: {result.get('memory_used', False)}")
        print(f"Memory Stored: {result.get('memory_stored', False)}")
        
        # Wait a bit between queries
        await asyncio.sleep(1)


async def test_different_sessions():
    """Test that different sessions maintain separate contexts"""
    print("\n" + "="*80)
    print("TEST 3: Different Sessions (Separate Contexts)")
    print("="*80)
    
    actor_id = "test-user-003"
    
    # Session 1
    print("\n--- Session 1 ---")
    payload1 = {
        "prompt": "Tell me about roaming charges",
        "actor_id": actor_id,
        "session_id": "session-A"
    }
    result1 = await agent_module.agent_invocation(payload1, {})
    print(f"Query: {payload1['prompt']}")
    print(f"Response: {result1['result'][:150]}...")
    
    # Session 2 (different topic)
    print("\n--- Session 2 ---")
    payload2 = {
        "prompt": "What is data activation?",
        "actor_id": actor_id,
        "session_id": "session-B"
    }
    result2 = await agent_module.agent_invocation(payload2, {})
    print(f"Query: {payload2['prompt']}")
    print(f"Response: {result2['result'][:150]}...")
    
    # Back to Session 1 (should remember roaming context)
    print("\n--- Back to Session 1 ---")
    payload3 = {
        "prompt": "How much does it cost?",
        "actor_id": actor_id,
        "session_id": "session-A"
    }
    result3 = await agent_module.agent_invocation(payload3, {})
    print(f"Query: {payload3['prompt']}")
    print(f"Response: {result3['result'][:150]}...")
    print(f"Memory Used: {result3.get('memory_used', False)} (should be True)")


async def test_error_handling():
    """Test error handling with invalid inputs"""
    print("\n" + "="*80)
    print("TEST 4: Error Handling")
    print("="*80)
    
    # Test with empty query
    print("\n--- Empty Query ---")
    payload = {
        "prompt": "",
        "actor_id": "test-user-004",
        "session_id": "test-session-004"
    }
    result = await agent_module.agent_invocation(payload, {})
    print(f"Response: {result['result'][:150]}...")
    
    # Test with missing actor_id (should use default)
    print("\n--- Missing Actor ID ---")
    payload = {
        "prompt": "What is roaming?",
        "session_id": "test-session-005"
    }
    result = await agent_module.agent_invocation(payload, {})
    print(f"Actor ID used: {result['actor_id']}")
    print(f"Response: {result['result'][:150]}...")


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("QNA SPECIALIST AGENT - MCP MEMORY INTEGRATION TESTS")
    print("="*80)
    
    # Check environment variables
    print("\nEnvironment Configuration:")
    print(f"GROQ_API_KEY: {'✓ Set' if os.getenv('GROQ_API_KEY') else '✗ Not Set'}")
    print(f"MCP_MEMORY_SERVER_ARN: {os.getenv('MCP_MEMORY_SERVER_ARN', 'Not Set')}")
    
    if not os.getenv('GROQ_API_KEY'):
        print("\n⚠️  WARNING: GROQ_API_KEY not set. Tests may fail.")
        return
    
    if not os.getenv('MCP_MEMORY_SERVER_ARN'):
        print("\n⚠️  WARNING: MCP_MEMORY_SERVER_ARN not set. Memory operations will fail.")
        print("   The agent will still work but without memory context.")
    
    try:
        # Run tests
        await test_single_query()
        await asyncio.sleep(2)
        
        await test_multi_turn_conversation()
        await asyncio.sleep(2)
        
        await test_different_sessions()
        await asyncio.sleep(2)
        
        await test_error_handling()
        
        print("\n" + "="*80)
        print("ALL TESTS COMPLETED")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup (AgentCore SDK client doesn't need explicit close)
        logger.info("Tests completed")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
