#!/usr/bin/env python3
"""
MCP Node Caller - Invoke AgentCore Agent from MCP Server

This script allows an MCP server to call an AgentCore agent runtime.
Use case: MCP server needs to invoke an agent to process requests.

Example: Memory MCP server calls QNA agent to answer questions
"""

import os
import json
import logging
import itertools
from typing import Dict, Any, Optional
from urllib.parse import quote

import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("mcp.node.caller")

# JSON-RPC ID counter (for MCP protocol)
_jsonrpc_id = itertools.count(1)

# Configuration
QNA_AGENT_ARN = os.getenv(
    "QNA_AGENT_ARN",
    "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_qna_agent-LuJi165oYZ"
)
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")


class AgentCoreCaller:
    """Call AgentCore agents from MCP servers or other services"""
    
    def __init__(
        self,
        agent_arn: str,
        region: str = "us-east-1",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None
    ):
        self.agent_arn = agent_arn
        self.region = region
        
        # Initialize AWS session
        if aws_access_key_id and aws_secret_access_key:
            self.session = boto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region
            )
        else:
            self.session = boto3.Session(region_name=region)
        
        self.credentials = self.session.get_credentials()
        
        if not self.credentials:
            raise ValueError("AWS credentials are required but not found")
        
        # Build invocation URL
        encoded_arn = quote(agent_arn, safe='')
        self.invoke_url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
        
        logger.info(f"Initialized caller for agent: {agent_arn}")
    
    def invoke_agent(
        self,
        prompt: str,
        actor_id: Optional[str] = None,
        session_id: Optional[str] = None,
        enable_memory: bool = True,
        timeout: float = 60.0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Invoke an AgentCore agent
        
        Args:
            prompt: The user query/prompt
            actor_id: Actor identifier (for memory)
            session_id: Session identifier (for memory)
            enable_memory: Whether to use memory
            timeout: Request timeout in seconds
            **kwargs: Additional parameters to pass to agent
            
        Returns:
            Agent response dictionary
        """
        # Build payload
        payload = {
            "prompt": prompt,
            "query": prompt,  # Some agents use 'query' instead
        }
        
        if actor_id:
            payload["actor_id"] = actor_id
        
        if session_id:
            payload["session_id"] = session_id
        
        if not enable_memory:
            payload["enable_memory"] = False
        
        # Add any additional parameters
        payload.update(kwargs)
        
        body = json.dumps(payload).encode("utf-8")
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Create and sign request
        request = AWSRequest(method="POST", url=self.invoke_url, data=body, headers=headers)
        SigV4Auth(self.credentials, "bedrock-agentcore", self.region).add_auth(request)
        
        logger.info(f"Invoking agent with prompt: {prompt[:50]}...")
        
        # Execute request
        try:
            response = requests.post(
                self.invoke_url,
                headers=dict(request.headers),
                data=body,
                timeout=timeout
            )
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            logger.info("Agent invocation successful")
            return result
            
        except requests.exceptions.Timeout:
            logger.error(f"Agent invocation timed out after {timeout}s")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"Agent invocation failed: HTTP {e.response.status_code}")
            logger.error(f"Response: {e.response.text[:200]}")
            raise
        except Exception as e:
            logger.error(f"Agent invocation failed: {e}")
            raise
    
    def invoke_agent_simple(self, prompt: str) -> str:
        """
        Simple invocation that returns just the answer text
        
        Args:
            prompt: The user query
            
        Returns:
            Answer text string
        """
        result = self.invoke_agent(prompt)
        
        # Extract answer from various possible response formats
        if isinstance(result, dict):
            # Try common response fields
            answer = (
                result.get("result") or
                result.get("answer") or
                result.get("response") or
                result.get("output") or
                str(result)
            )
            return answer
        
        return str(result)


class MCPNodeCaller:
    """
    MCP-specific caller that wraps agent invocation in MCP protocol
    
    Use this when calling from an MCP server that needs to maintain
    MCP protocol compatibility.
    """
    
    def __init__(self, agent_arn: str, region: str = "us-east-1"):
        self.caller = AgentCoreCaller(
            agent_arn=agent_arn,
            region=region,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
    
    def call_as_mcp_tool(
        self,
        prompt: str,
        actor_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call agent and return MCP-formatted response
        
        Returns:
            MCP tool response format
        """
        try:
            result = self.caller.invoke_agent(
                prompt=prompt,
                actor_id=actor_id,
                session_id=session_id
            )
            
            # Format as MCP tool response
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ],
                "isError": False
            }
            
        except Exception as e:
            logger.error(f"MCP tool call failed: {e}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "error": str(e),
                            "error_type": type(e).__name__
                        })
                    }
                ],
                "isError": True
            }
    
    def call_as_jsonrpc(
        self,
        prompt: str,
        actor_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call agent and return JSON-RPC formatted response
        
        Returns:
            JSON-RPC response format
        """
        try:
            result = self.caller.invoke_agent(
                prompt=prompt,
                actor_id=actor_id,
                session_id=session_id
            )
            
            return {
                "jsonrpc": "2.0",
                "id": next(_jsonrpc_id),
                "result": result
            }
            
        except Exception as e:
            logger.error(f"JSON-RPC call failed: {e}")
            return {
                "jsonrpc": "2.0",
                "id": next(_jsonrpc_id),
                "error": {
                    "code": -32603,
                    "message": str(e),
                    "data": {
                        "error_type": type(e).__name__
                    }
                }
            }


# Example usage functions

def example_simple_call():
    """Example: Simple agent call"""
    print("="*80)
    print("Example 1: Simple Agent Call")
    print("="*80)
    
    caller = AgentCoreCaller(QNA_AGENT_ARN, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    
    prompt = "What is bottle gourd?"
    print(f"\nPrompt: {prompt}")
    
    try:
        answer = caller.invoke_agent_simple(prompt)
        print(f"\nAnswer: {answer}")
    except Exception as e:
        print(f"\nError: {e}")


def example_detailed_call():
    """Example: Detailed agent call with memory"""
    print("\n" + "="*80)
    print("Example 2: Detailed Agent Call with Memory")
    print("="*80)
    
    caller = AgentCoreCaller(QNA_AGENT_ARN, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    
    prompt = "How do I activate my service?"
    actor_id = "test-user-123"
    session_id = "test-session-456"
    
    print(f"\nPrompt: {prompt}")
    print(f"Actor ID: {actor_id}")
    print(f"Session ID: {session_id}")
    
    try:
        result = caller.invoke_agent(
            prompt=prompt,
            actor_id=actor_id,
            session_id=session_id,
            enable_memory=True
        )
        
        print(f"\nFull Response:")
        print(json.dumps(result, indent=2))
        
        # Extract specific fields
        if isinstance(result, dict):
            print(f"\nAnswer: {result.get('result', 'N/A')}")
            print(f"Memory Used: {result.get('memory_used', 'N/A')}")
            print(f"Memory Stored: {result.get('memory_stored', 'N/A')}")
            
    except Exception as e:
        print(f"\nError: {e}")


def example_mcp_tool_call():
    """Example: Call as MCP tool"""
    print("\n" + "="*80)
    print("Example 3: MCP Tool Call")
    print("="*80)
    
    mcp_caller = MCPNodeCaller(QNA_AGENT_ARN, AWS_REGION)
    
    prompt = "What are the pricing options?"
    
    print(f"\nPrompt: {prompt}")
    
    result = mcp_caller.call_as_mcp_tool(
        prompt=prompt,
        actor_id="mcp-user",
        session_id="mcp-session"
    )
    
    print(f"\nMCP Tool Response:")
    print(json.dumps(result, indent=2))


def example_jsonrpc_call():
    """Example: Call as JSON-RPC"""
    print("\n" + "="*80)
    print("Example 4: JSON-RPC Call")
    print("="*80)
    
    mcp_caller = MCPNodeCaller(QNA_AGENT_ARN, AWS_REGION)
    
    prompt = "Tell me about troubleshooting"
    
    print(f"\nPrompt: {prompt}")
    
    result = mcp_caller.call_as_jsonrpc(
        prompt=prompt,
        actor_id="jsonrpc-user",
        session_id="jsonrpc-session"
    )
    
    print(f"\nJSON-RPC Response:")
    print(json.dumps(result, indent=2))


def example_batch_calls():
    """Example: Multiple calls in sequence"""
    print("\n" + "="*80)
    print("Example 5: Batch Calls")
    print("="*80)
    
    caller = AgentCoreCaller(QNA_AGENT_ARN, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    
    prompts = [
        "What is bottle gourd?",
        "How do I activate my service?",
        "What are the pricing options?"
    ]
    
    actor_id = "batch-user"
    session_id = "batch-session"
    
    print(f"\nProcessing {len(prompts)} prompts...")
    print(f"Actor ID: {actor_id}")
    print(f"Session ID: {session_id}")
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n--- Query {i} ---")
        print(f"Prompt: {prompt}")
        
        try:
            answer = caller.invoke_agent_simple(
                prompt=prompt
            )
            print(f"Answer: {answer[:100]}...")
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Run all examples"""
    print("="*80)
    print("MCP NODE CALLER - EXAMPLES")
    print("="*80)
    print(f"\nAgent ARN: {QNA_AGENT_ARN}")
    print(f"Region: {AWS_REGION}")
    print()
    
    # Run examples
    example_simple_call()
    example_detailed_call()
    example_mcp_tool_call()
    example_jsonrpc_call()
    example_batch_calls()
    
    print("\n" + "="*80)
    print("All examples completed!")
    print("="*80)


if __name__ == "__main__":
    main()
