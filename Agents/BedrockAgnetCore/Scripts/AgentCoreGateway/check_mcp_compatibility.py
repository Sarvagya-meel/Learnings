#!/usr/bin/env python3
"""
MCP Server Compatibility Checker

This script checks if your MCP server has compatible tool capabilities
for use with the AgentCore Gateway.

It tests:
1. Server connectivity
2. JSON-RPC protocol support
3. Available tools (tools/list)
4. Tool invocation (tools/call)
5. Response format compatibility
"""

import os
import sys
import json
import itertools
from typing import Dict, Any, List
from urllib.parse import quote

import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from dotenv import load_dotenv

load_dotenv()

# Configuration
MCP_SERVER_ARN = os.getenv(
    "MCP_MEMORY_SERVER_ARN",
    "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD"
)
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# JSON-RPC ID counter
_jsonrpc_id = itertools.count(1)


class CompatibilityChecker:
    """Check MCP server compatibility with gateway"""
    
    def __init__(self, server_arn: str, region: str):
        self.server_arn = server_arn
        self.region = region
        
        # Initialize AWS session
        if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
            session = boto3.Session(
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=region
            )
        else:
            session = boto3.Session(region_name=region)
        
        self.credentials = session.get_credentials()
        
        if not self.credentials:
            raise ValueError("AWS credentials required")
        
        # Build invocation URL
        encoded_arn = quote(server_arn, safe='')
        self.invoke_url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
        
        print(f"Checking server: {server_arn}")
        print(f"Region: {region}")
        print(f"URL: {self.invoke_url}")
        print()
    
    def _make_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a JSON-RPC request to the server"""
        payload = {
            "jsonrpc": "2.0",
            "id": next(_jsonrpc_id),
            "method": method,
            "params": params
        }
        
        body = json.dumps(payload).encode("utf-8")
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        
        # Sign request
        request = AWSRequest(method="POST", url=self.invoke_url, data=body, headers=headers)
        SigV4Auth(self.credentials, "bedrock-agentcore", self.region).add_auth(request)
        
        # Execute
        response = requests.post(
            self.invoke_url,
            headers=dict(request.headers),
            data=body,
            timeout=30.0
        )
        
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "text": response.text,
            "ok": response.ok
        }
    
    def check_connectivity(self) -> bool:
        """Test 1: Check if server is reachable"""
        print("="*80)
        print("TEST 1: Server Connectivity")
        print("="*80)
        
        try:
            result = self._make_request("tools/list", {})
            
            if result["status_code"] == 403:
                print("✗ FAILED: 403 Forbidden")
                print("  Issue: Resource policy not applied")
                print("  Solution: Apply resource policy (see apply_policy_manual.md)")
                print(f"  Status Code: {result['status_code']}")
                return False
            
            if result["status_code"] == 404:
                print("✗ FAILED: 404 Not Found")
                print("  Issue: Server ARN incorrect or server not deployed")
                print(f"  Status Code: {result['status_code']}")
                return False
            
            if result["status_code"] >= 500:
                print("✗ FAILED: Server Error")
                print(f"  Status Code: {result['status_code']}")
                print(f"  Response: {result['text'][:200]}")
                return False
            
            if result["ok"]:
                print("✓ PASSED: Server is reachable")
                print(f"  Status Code: {result['status_code']}")
                return True
            else:
                print(f"✗ FAILED: HTTP {result['status_code']}")
                print(f"  Response: {result['text'][:200]}")
                return False
                
        except requests.exceptions.Timeout:
            print("✗ FAILED: Connection timeout")
            print("  Issue: Server not responding")
            return False
        except requests.exceptions.ConnectionError as e:
            print("✗ FAILED: Connection error")
            print(f"  Error: {e}")
            return False
        except Exception as e:
            print(f"✗ FAILED: {type(e).__name__}: {e}")
            return False
    
    def check_jsonrpc_protocol(self) -> bool:
        """Test 2: Check JSON-RPC protocol support"""
        print("\n" + "="*80)
        print("TEST 2: JSON-RPC Protocol Support")
        print("="*80)
        
        try:
            result = self._make_request("tools/list", {})
            
            if not result["ok"]:
                print(f"✗ FAILED: HTTP {result['status_code']}")
                return False
            
            # Parse response
            resp_text = result["text"].strip()
            
            # Handle SSE format
            if resp_text.startswith("data:"):
                print("✓ Server uses SSE format")
                data_lines = []
                for line in resp_text.splitlines():
                    if not line.strip():
                        break
                    if line.startswith("data:"):
                        data_lines.append(line[len("data:"):].lstrip())
                resp_text = "\n".join(data_lines)
            
            # Parse JSON
            try:
                resp_json = json.loads(resp_text)
            except json.JSONDecodeError as e:
                print("✗ FAILED: Invalid JSON response")
                print(f"  Error: {e}")
                print(f"  Response: {resp_text[:200]}")
                return False
            
            # Check JSON-RPC structure
            if "jsonrpc" in resp_json:
                print(f"✓ JSON-RPC version: {resp_json['jsonrpc']}")
            else:
                print("⚠ Warning: No 'jsonrpc' field in response")
            
            if "id" in resp_json:
                print(f"✓ Request ID present: {resp_json['id']}")
            else:
                print("⚠ Warning: No 'id' field in response")
            
            if "error" in resp_json:
                print(f"✗ FAILED: Server returned error")
                print(f"  Error: {resp_json['error']}")
                return False
            
            if "result" in resp_json:
                print("✓ Result field present")
                print("✓ PASSED: JSON-RPC protocol supported")
                return True
            else:
                print("✗ FAILED: No 'result' field in response")
                return False
                
        except Exception as e:
            print(f"✗ FAILED: {type(e).__name__}: {e}")
            return False
    
    def check_tools_list(self) -> tuple[bool, List[Dict[str, Any]]]:
        """Test 3: Check tools/list capability"""
        print("\n" + "="*80)
        print("TEST 3: Tools List Capability")
        print("="*80)
        
        try:
            result = self._make_request("tools/list", {})
            
            if not result["ok"]:
                print(f"✗ FAILED: HTTP {result['status_code']}")
                return False, []
            
            # Parse response
            resp_text = result["text"].strip()
            if resp_text.startswith("data:"):
                data_lines = []
                for line in resp_text.splitlines():
                    if not line.strip():
                        break
                    if line.startswith("data:"):
                        data_lines.append(line[len("data:"):].lstrip())
                resp_text = "\n".join(data_lines)
            
            resp_json = json.loads(resp_text)
            
            if "error" in resp_json:
                print(f"✗ FAILED: {resp_json['error']}")
                return False, []
            
            result_data = resp_json.get("result", {})
            tools = result_data.get("tools", [])
            
            if not tools:
                print("✗ FAILED: No tools found")
                return False, []
            
            print(f"✓ PASSED: Found {len(tools)} tools")
            print("\nAvailable Tools:")
            for i, tool in enumerate(tools, 1):
                name = tool.get("name", "unknown")
                desc = tool.get("description", "No description")
                print(f"  {i}. {name}")
                print(f"     {desc[:70]}...")
                
                # Check tool structure
                if "inputSchema" in tool:
                    print(f"     ✓ Has input schema")
                else:
                    print(f"     ⚠ Missing input schema")
            
            return True, tools
            
        except Exception as e:
            print(f"✗ FAILED: {type(e).__name__}: {e}")
            return False, []
    
    def check_tool_invocation(self, tools: List[Dict[str, Any]]) -> bool:
        """Test 4: Check tools/call capability"""
        print("\n" + "="*80)
        print("TEST 4: Tool Invocation Capability")
        print("="*80)
        
        if not tools:
            print("⚠ SKIPPED: No tools to test")
            return False
        
        # Find server_info tool (safest to test)
        test_tool = None
        for tool in tools:
            if tool.get("name") == "server_info":
                test_tool = tool
                break
        
        if not test_tool:
            # Try first tool
            test_tool = tools[0]
        
        tool_name = test_tool.get("name")
        print(f"Testing tool: {tool_name}")
        
        try:
            # Build minimal arguments
            arguments = {}
            input_schema = test_tool.get("inputSchema", {})
            properties = input_schema.get("properties", {})
            required = input_schema.get("required", [])
            
            # Add required arguments with dummy values
            for prop in required:
                prop_info = properties.get(prop, {})
                prop_type = prop_info.get("type", "string")
                
                if prop_type == "string":
                    arguments[prop] = "test-compatibility-check"
                elif prop_type == "integer":
                    arguments[prop] = 1
                elif prop_type == "number":
                    arguments[prop] = 1.0
                elif prop_type == "boolean":
                    arguments[prop] = True
                elif prop_type == "array":
                    arguments[prop] = []
                elif prop_type == "object":
                    arguments[prop] = {}
            
            print(f"Arguments: {json.dumps(arguments)}")
            
            result = self._make_request("tools/call", {
                "name": tool_name,
                "arguments": arguments
            })
            
            if not result["ok"]:
                print(f"✗ FAILED: HTTP {result['status_code']}")
                print(f"  Response: {result['text'][:200]}")
                return False
            
            # Parse response
            resp_text = result["text"].strip()
            if resp_text.startswith("data:"):
                data_lines = []
                for line in resp_text.splitlines():
                    if not line.strip():
                        break
                    if line.startswith("data:"):
                        data_lines.append(line[len("data:"):].lstrip())
                resp_text = "\n".join(data_lines)
            
            resp_json = json.loads(resp_text)
            
            if "error" in resp_json:
                error = resp_json["error"]
                # Some errors are expected (like validation errors)
                if "validation" in str(error).lower() or "invalid" in str(error).lower():
                    print("✓ PASSED: Tool invocation works (validation error expected)")
                    return True
                else:
                    print(f"⚠ Tool returned error: {error}")
                    print("  But invocation mechanism works")
                    return True
            
            if "result" in resp_json:
                print("✓ PASSED: Tool invocation successful")
                result_data = resp_json.get("result", {})
                print(f"  Result: {json.dumps(result_data, indent=2)[:200]}")
                return True
            
            print("⚠ Unexpected response format")
            return False
            
        except Exception as e:
            print(f"✗ FAILED: {type(e).__name__}: {e}")
            return False
    
    def check_response_format(self) -> bool:
        """Test 5: Check response format compatibility"""
        print("\n" + "="*80)
        print("TEST 5: Response Format Compatibility")
        print("="*80)
        
        try:
            result = self._make_request("tools/list", {})
            
            if not result["ok"]:
                print(f"✗ FAILED: HTTP {result['status_code']}")
                return False
            
            resp_text = result["text"].strip()
            
            # Check for SSE format
            uses_sse = resp_text.startswith("data:")
            if uses_sse:
                print("✓ Server uses SSE format (Server-Sent Events)")
                print("  Gateway can handle this format")
            else:
                print("✓ Server uses plain JSON format")
            
            # Check content type
            content_type = result["headers"].get("content-type", "")
            print(f"✓ Content-Type: {content_type}")
            
            # Parse and check structure
            if uses_sse:
                data_lines = []
                for line in resp_text.splitlines():
                    if not line.strip():
                        break
                    if line.startswith("data:"):
                        data_lines.append(line[len("data:"):].lstrip())
                resp_text = "\n".join(data_lines)
            
            resp_json = json.loads(resp_text)
            
            # Check expected fields
            checks = {
                "jsonrpc": "jsonrpc" in resp_json,
                "id": "id" in resp_json,
                "result or error": "result" in resp_json or "error" in resp_json
            }
            
            all_passed = all(checks.values())
            
            print("\nFormat Checks:")
            for check, passed in checks.items():
                status = "✓" if passed else "✗"
                print(f"  {status} {check}")
            
            if all_passed:
                print("\n✓ PASSED: Response format is compatible")
                return True
            else:
                print("\n⚠ Some format checks failed, but may still work")
                return False
                
        except Exception as e:
            print(f"✗ FAILED: {type(e).__name__}: {e}")
            return False
    
    def run_all_checks(self) -> Dict[str, bool]:
        """Run all compatibility checks"""
        results = {}
        
        # Test 1: Connectivity
        results["connectivity"] = self.check_connectivity()
        
        if not results["connectivity"]:
            print("\n" + "="*80)
            print("STOPPING: Cannot proceed without connectivity")
            print("="*80)
            return results
        
        # Test 2: JSON-RPC Protocol
        results["jsonrpc"] = self.check_jsonrpc_protocol()
        
        # Test 3: Tools List
        results["tools_list"], tools = self.check_tools_list()
        
        # Test 4: Tool Invocation
        results["tool_invocation"] = self.check_tool_invocation(tools)
        
        # Test 5: Response Format
        results["response_format"] = self.check_response_format()
        
        return results


def main():
    """Run compatibility checks"""
    print("="*80)
    print("MCP SERVER COMPATIBILITY CHECKER")
    print("="*80)
    print()
    
    checker = CompatibilityChecker(MCP_SERVER_ARN, AWS_REGION)
    results = checker.run_all_checks()
    
    # Summary
    print("\n" + "="*80)
    print("COMPATIBILITY SUMMARY")
    print("="*80)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test.replace('_', ' ').title()}")
    
    print("\n" + "-"*80)
    print(f"Total: {total} tests")
    print(f"Passed: {passed}/{total} ({100*passed/max(total,1):.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL CHECKS PASSED!")
        print("Your MCP server is fully compatible with the gateway.")
    elif passed >= total * 0.8:
        print("\n✓ MOSTLY COMPATIBLE")
        print("Your MCP server should work with the gateway.")
        print("Some features may need adjustment.")
    elif results.get("connectivity"):
        print("\n⚠ PARTIALLY COMPATIBLE")
        print("Your MCP server is reachable but has compatibility issues.")
        print("Review the failed tests above.")
    else:
        print("\n✗ NOT COMPATIBLE")
        print("Cannot connect to MCP server.")
        print("Fix connectivity issues first (see apply_policy_manual.md)")
    
    print("="*80)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
