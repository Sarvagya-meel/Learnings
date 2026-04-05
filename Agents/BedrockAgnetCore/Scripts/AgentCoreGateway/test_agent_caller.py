#!/usr/bin/env python3
"""
Quick test script for MCP Node Caller

Tests if you can successfully invoke your QNA agent.
"""

import os
import sys
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from mcp_node_caller import AgentCoreCaller

load_dotenv()

# Configuration
QNA_AGENT_ARN = os.getenv(
    "QNA_AGENT_ARN",
    "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_qna_agent-LuJi165oYZ"
)
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")


def test_simple_call():
    """Test 1: Simple agent call"""
    print("="*80)
    print("TEST 1: Simple Agent Call")
    print("="*80)
    
    try:
        caller = AgentCoreCaller(
            agent_arn=QNA_AGENT_ARN,
            region=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        print("✓ Caller initialized")
        
        prompt = "What is bottle gourd?"
        print(f"\nPrompt: {prompt}")
        
        answer = caller.invoke_agent_simple(prompt)
        
        print(f"\n✓ SUCCESS!")
        print(f"Answer: {answer[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        return False


def test_detailed_call():
    """Test 2: Detailed call with memory"""
    print("\n" + "="*80)
    print("TEST 2: Detailed Call with Memory")
    print("="*80)
    
    try:
        caller = AgentCoreCaller(
            agent_arn=QNA_AGENT_ARN,
            region=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        prompt = "How do I activate my service?"
        actor_id = "test-user"
        session_id = "test-session"
        
        print(f"Prompt: {prompt}")
        print(f"Actor ID: {actor_id}")
        print(f"Session ID: {session_id}")
        
        result = caller.invoke_agent(
            prompt=prompt,
            actor_id=actor_id,
            session_id=session_id,
            enable_memory=True
        )
        
        print(f"\n✓ SUCCESS!")
        print(f"Answer: {result.get('result', 'N/A')[:200]}...")
        print(f"Memory Used: {result.get('memory_used', 'N/A')}")
        print(f"Memory Stored: {result.get('memory_stored', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        return False


def main():
    """Run tests"""
    print("="*80)
    print("MCP NODE CALLER - QUICK TEST")
    print("="*80)
    print(f"\nAgent ARN: {QNA_AGENT_ARN}")
    print(f"Region: {AWS_REGION}")
    print()
    
    results = []
    
    # Test 1
    results.append(("Simple Call", test_simple_call()))
    
    # Test 2
    results.append(("Detailed Call", test_detailed_call()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {total} tests")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("Your agent caller is working correctly.")
        print("\nNext steps:")
        print("1. Read MCP_NODE_CALLER_GUIDE.md")
        print("2. Integrate into your MCP server")
        print("3. See mcp_server_with_agent_caller.py for examples")
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("\nTroubleshooting:")
        print("1. Check your .env file has correct credentials")
        print("2. Verify agent ARN is correct")
        print("3. Check IAM permissions (bedrock-agentcore:InvokeRuntime)")
        print("4. Check agent is deployed and running")
    
    print("="*80)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
