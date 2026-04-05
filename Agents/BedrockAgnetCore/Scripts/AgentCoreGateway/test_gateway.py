#!/usr/bin/env python3
"""
Test script for AgentCore Gateway

This script tests all gateway functionality:
1. Server registration
2. Tool listing
3. Server health check
4. Memory storage
5. Memory retrieval
"""

import os
import sys
import json
import asyncio
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from agentcore_gateway import AgentCoreGateway

load_dotenv()

# Configuration
MCP_SERVER_ARN = os.getenv(
    "MCP_MEMORY_SERVER_ARN",
    "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD"
)
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# Test data
TEST_ACTOR_ID = "gateway-test-user"
TEST_SESSION_ID = "gateway-test-session"


class TestResult:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def add(self, name: str, success: bool, message: str = ""):
        self.tests.append({
            "name": name,
            "success": success,
            "message": message
        })
        if success:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_summary(self):
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        for test in self.tests:
            status = "✓ PASS" if test["success"] else "✗ FAIL"
            print(f"{status}: {test['name']}")
            if test["message"]:
                print(f"       {test['message']}")
        
        print("\n" + "-"*80)
        print(f"Total: {len(self.tests)} tests")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print("="*80)
        
        return self.failed == 0


def test_gateway_initialization():
    """Test 1: Gateway initialization"""
    print("\n" + "="*80)
    print("TEST 1: Gateway Initialization")
    print("="*80)
    
    result = TestResult()
    
    try:
        gateway = AgentCoreGateway(
            region=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        print("✓ Gateway initialized successfully")
        result.add("Gateway initialization", True)
        return gateway, result
    except Exception as e:
        print(f"✗ Gateway initialization failed: {e}")
        result.add("Gateway initialization", False, str(e))
        return None, result


def test_server_registration(gateway):
    """Test 2: Server registration"""
    print("\n" + "="*80)
    print("TEST 2: Server Registration")
    print("="*80)
    
    result = TestResult()
    
    try:
        gateway.register_server(
            name="memory",
            arn=MCP_SERVER_ARN,
            description="AgentCore Memory MCP Server",
            tags=["memory", "storage", "context"]
        )
        print(f"✓ Server registered: memory")
        print(f"  ARN: {MCP_SERVER_ARN}")
        result.add("Server registration", True)
        
        # Verify registration
        if "memory" in gateway.servers:
            print("✓ Server found in registry")
            result.add("Server in registry", True)
        else:
            print("✗ Server not found in registry")
            result.add("Server in registry", False)
        
        return result
    except Exception as e:
        print(f"✗ Server registration failed: {e}")
        result.add("Server registration", False, str(e))
        return result


def test_list_tools(gateway):
    """Test 3: List available tools"""
    print("\n" + "="*80)
    print("TEST 3: List Available Tools")
    print("="*80)
    
    result = TestResult()
    
    try:
        tools = gateway.list_tools("memory", timeout=30.0)
        print(f"✓ Retrieved {len(tools)} tools")
        result.add("List tools", True, f"Found {len(tools)} tools")
        
        # Check for expected tools
        expected_tools = ["retrieve_memory", "store_interaction", "server_info"]
        tool_names = [t.get("name") for t in tools]
        
        for expected in expected_tools:
            if expected in tool_names:
                print(f"  ✓ {expected}")
                result.add(f"Tool: {expected}", True)
            else:
                print(f"  ✗ {expected} (missing)")
                result.add(f"Tool: {expected}", False, "Tool not found")
        
        # Print tool details
        print("\nTool Details:")
        for tool in tools:
            name = tool.get("name", "unknown")
            desc = tool.get("description", "No description")
            print(f"  - {name}")
            print(f"    {desc[:80]}...")
        
        return result
    except Exception as e:
        print(f"✗ List tools failed: {e}")
        result.add("List tools", False, str(e))
        return result


def test_server_info(gateway):
    """Test 4: Get server info (health check)"""
    print("\n" + "="*80)
    print("TEST 4: Server Health Check")
    print("="*80)
    
    result = TestResult()
    
    try:
        info = gateway.get_server_info("memory", session_id="test-health-check")
        print("✓ Server info retrieved")
        result.add("Server health check", True)
        
        # Print server info
        print("\nServer Info:")
        print(json.dumps(info, indent=2, default=str))
        
        return result
    except Exception as e:
        print(f"✗ Server health check failed: {e}")
        result.add("Server health check", False, str(e))
        return result


def test_store_interaction(gateway):
    """Test 5: Store interaction"""
    print("\n" + "="*80)
    print("TEST 5: Store Interaction")
    print("="*80)
    
    result = TestResult()
    
    test_cases = [
        {
            "user_msg": "What is AgentCore?",
            "assistant_msg": "AgentCore is AWS's framework for building AI agents with memory and tool capabilities.",
        },
        {
            "user_msg": "How do I deploy an agent?",
            "assistant_msg": "You can deploy an agent using the bedrock-agentcore CLI with the 'deploy' command.",
        },
        {
            "user_msg": "What is an MCP server?",
            "assistant_msg": "An MCP (Model Context Protocol) server provides tools and resources that agents can use.",
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        try:
            store_result = gateway.invoke_mcp_tool(
                server_name="memory",
                tool_name="store_interaction",
                arguments={
                    "user_msg": test_case["user_msg"],
                    "assistant_msg": test_case["assistant_msg"],
                    "actor_id": TEST_ACTOR_ID,
                    "session_id": TEST_SESSION_ID
                }
            )
            
            print(f"✓ Test case {i} stored")
            print(f"  User: {test_case['user_msg'][:50]}...")
            result.add(f"Store interaction {i}", True)
            
        except Exception as e:
            print(f"✗ Test case {i} failed: {e}")
            result.add(f"Store interaction {i}", False, str(e))
    
    return result


def test_retrieve_memory(gateway):
    """Test 6: Retrieve memory"""
    print("\n" + "="*80)
    print("TEST 6: Retrieve Memory")
    print("="*80)
    
    result = TestResult()
    
    test_queries = [
        "AgentCore",
        "deploy agent",
        "MCP server"
    ]
    
    for i, query in enumerate(test_queries, 1):
        try:
            retrieve_result = gateway.invoke_mcp_tool(
                server_name="memory",
                tool_name="retrieve_memory",
                arguments={
                    "query": query,
                    "max_results": 3,
                    "actor_id": TEST_ACTOR_ID,
                    "session_id": TEST_SESSION_ID
                }
            )
            
            # Parse result
            content = retrieve_result.get("structuredContent", {}).get("result", {}).get("content", [{}])
            if content:
                text = content[0].get("text", "{}")
                data = json.loads(text) if isinstance(text, str) else text
                items = data.get("data", {}).get("items", [])
                
                print(f"✓ Query {i}: '{query}' - Found {len(items)} memories")
                result.add(f"Retrieve memory {i}", True, f"Found {len(items)} items")
                
                # Print memory details
                for j, item in enumerate(items, 1):
                    content_text = item.get("content", "")[:60]
                    relevance = item.get("relevance", 0.0)
                    print(f"  {j}. {content_text}... (relevance: {relevance:.3f})")
            else:
                print(f"✓ Query {i}: '{query}' - No memories found")
                result.add(f"Retrieve memory {i}", True, "No items found")
            
        except Exception as e:
            print(f"✗ Query {i} failed: {e}")
            result.add(f"Retrieve memory {i}", False, str(e))
    
    return result


def test_error_handling(gateway):
    """Test 7: Error handling"""
    print("\n" + "="*80)
    print("TEST 7: Error Handling")
    print("="*80)
    
    result = TestResult()
    
    # Test 1: Invalid server name
    try:
        gateway.invoke_mcp_tool(
            server_name="nonexistent",
            tool_name="retrieve_memory",
            arguments={}
        )
        print("✗ Should have raised error for invalid server")
        result.add("Invalid server error", False, "No error raised")
    except ValueError as e:
        print(f"✓ Correctly raised error for invalid server: {e}")
        result.add("Invalid server error", True)
    except Exception as e:
        print(f"✗ Unexpected error type: {e}")
        result.add("Invalid server error", False, f"Wrong error type: {type(e)}")
    
    # Test 2: Invalid arguments
    try:
        gateway.invoke_mcp_tool(
            server_name="memory",
            tool_name="retrieve_memory",
            arguments={
                "query": "",  # Empty query should fail
                "max_results": 5,
                "actor_id": TEST_ACTOR_ID,
                "session_id": TEST_SESSION_ID
            }
        )
        print("✗ Should have raised error for empty query")
        result.add("Invalid arguments error", False, "No error raised")
    except Exception as e:
        print(f"✓ Correctly raised error for invalid arguments: {e}")
        result.add("Invalid arguments error", True)
    
    return result


def main():
    """Run all tests"""
    print("="*80)
    print("AGENTCORE GATEWAY TEST SUITE")
    print("="*80)
    print(f"Region: {AWS_REGION}")
    print(f"Server ARN: {MCP_SERVER_ARN}")
    print(f"Test Actor: {TEST_ACTOR_ID}")
    print(f"Test Session: {TEST_SESSION_ID}")
    
    all_results = []
    
    # Test 1: Initialize gateway
    gateway, result = test_gateway_initialization()
    all_results.append(result)
    
    if gateway is None:
        print("\n✗ Cannot continue tests without gateway")
        return False
    
    # Test 2: Register server
    result = test_server_registration(gateway)
    all_results.append(result)
    
    # Test 3: List tools
    result = test_list_tools(gateway)
    all_results.append(result)
    
    # Test 4: Server health check
    result = test_server_info(gateway)
    all_results.append(result)
    
    # Test 5: Store interactions
    result = test_store_interaction(gateway)
    all_results.append(result)
    
    # Test 6: Retrieve memory
    result = test_retrieve_memory(gateway)
    all_results.append(result)
    
    # Test 7: Error handling
    result = test_error_handling(gateway)
    all_results.append(result)
    
    # Print combined summary
    print("\n" + "="*80)
    print("OVERALL TEST SUMMARY")
    print("="*80)
    
    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)
    total_tests = total_passed + total_failed
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed} ({100*total_passed/max(total_tests,1):.1f}%)")
    print(f"Failed: {total_failed}")
    
    if total_failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("="*80)
        return True
    else:
        print(f"\n⚠️  {total_failed} TEST(S) FAILED")
        print("="*80)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
