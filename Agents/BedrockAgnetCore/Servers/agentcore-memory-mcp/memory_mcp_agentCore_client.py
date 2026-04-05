"""
Author: Sarvagya Meel
Email: sarvagyameel2@gmail.com
Date: 11/02/26
"""
import os
import itertools
import json
import uuid
from typing import Any, Dict, Optional
from pprint import pformat
import requests
import boto3
from botocore.session import get_session
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from urllib.parse import quote

from dotenv import load_dotenv

GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"


import inspect
from mcp.server.fastmcp.server import FastMCP
# print("FastMCP.run signature:", inspect.signature(FastMCP.run))
# print(inspect.getsource(FastMCP.run))
# print(inspect.getsource(FastMCP.run_streamable_http_async))


_id = itertools.count(1)

actor_id = "test_actor_1"
session_id = str(uuid.uuid4())
print(f"Session ID: {session_id}")

class MCPError(RuntimeError):
    pass


def pretty_print_mcp_from_r_text(r_text: str) -> Any:
    # Handles either plain JSON OR SSE with `data: {...}` JSON-RPC payloads.
    s = (r_text or "").strip()

    # Plain JSON case
    if s.startswith("{") or s.startswith("["):
        obj = json.loads(s)
        print(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True))
        return

    # SSE case: collect all `data:` lines up to the first blank line (one event)
    data_lines = []
    for line in r_text.splitlines():
        if not line.strip():  # blank line => end of event
            break
        if line.startswith("data:"):
            data_lines.append(line[len("data:"):].lstrip())

    if not data_lines:
        raise ValueError("No JSON found (no SSE data: lines).")

    obj = json.loads("\n".join(data_lines))
    print(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True))
    return obj

def print_tools(response, green=True):
    color_on = GREEN if green else ""
    color_off = RESET if green else ""

    for i, tool in enumerate(response.get("tools", []), start=1):
        name = tool.get("name")
        description = tool.get("description")
        input_schema = tool.get("inputSchema")
        output_schema = tool.get("outputSchema")

        header = f"\n=== Tool {i}: {name} ==="
        print(f"{color_on}{header}{color_off}")

        description = "Tool Description:\n" + pformat(description, width=100, sort_dicts=False)
        print(f"{color_on}{description}{color_off}")

        ins = "Tool inputSchema:\n" + pformat(input_schema, width=100, sort_dicts=False)
        print(f"{color_on}{ins}{color_off}")

        if isinstance(output_schema, str):
            try:
                output_schema = json.loads(output_schema)
            except json.JSONDecodeError:
                pass

        outs = "Tool outputSchema:\n" + pformat(output_schema, width=100, sort_dicts=False)
        print(f"{color_on}{outs}{color_off}")

def print_tool_response(response: Dict[str, Any]) -> None:
    is_error = bool(response.get("isError"))
    color = RED if is_error else GREEN
    label = "ERROR" if is_error else "SUCCESS"

    if is_error:
        pretty = json.dumps(response, indent=2, ensure_ascii=False)
        print(f"{color}[{label}] Full result:\n{pretty}{RESET}")
        return

    text = (
        response.get("structuredContent", {})
              .get("result", {})
              .get("content", [{}])[0]
              .get("text")
    )

    payload = None
    if isinstance(text, str):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = {"raw_text": text}
    elif isinstance(text, dict):
        payload = text

    data = (payload or {}).get("data",{}).get('items') if (payload or {}).get("data", {}).get('items', None) else payload
    pretty = pformat(data, width=100, sort_dicts=False)
    print(f"{color}[{label}]\n{pretty}{RESET}")


def jsonrpc_agentcore(url: str, method: str, params: Dict[str, Any],*,timeout_s: float = 60.0) -> Any:
    payload = {
        "jsonrpc": "2.0",
        "id": next(_id),
        "method": method,
        "params": params,
    }
    body = json.dumps(payload).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    session = boto3.Session(aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
    credentials = session.get_credentials()

    # Create the request with headers included
    request = AWSRequest(method="POST", url=url, data=body, headers=headers)

    # Sign the request (includes signing the headers)
    SigV4Auth(credentials, "bedrock-agentcore", REGION).add_auth(request)

    # Execute the request using the signed headers
    response = requests.post(url, headers=dict(request.headers), data=body, timeout=timeout_s)
    print(f"Status Code: {response.status_code}")
    response.raise_for_status()

    resp = pretty_print_mcp_from_r_text(response.text)

    if isinstance(resp, dict) and resp.get("error"):
        raise MCPError(f"JSON-RPC error: {resp['error']}")
    return resp.get("result") if isinstance(resp, dict) else resp

def list_tools(url: str) -> Any:
    response =  jsonrpc_agentcore(url, "tools/list", {})
    print_tools(response)
    return response


def call_tool(url: str, name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
    response = jsonrpc_agentcore(url, "tools/call", {"name": name, "arguments": arguments or {}})
    print_tool_response(response)
    return response


if __name__ == "__main__":
    # 1. Configuration
    RUNTIME_ARN = "arn:aws:bedrock-agentcore:us-east-1:662403250828:runtime/agentcore_memory_mcp_server-R4jmV6ERZD"
    REGION = "us-east-1"
    import os

    # Load environment variables from a .env file
    load_dotenv()
    ACCESS_KEY = os.getenv("AGENTCORE_ACCESS_KEY")
    SECRET_KEY = os.getenv("AGENTCORE_SECRET_KEY")
    # 2. Correct Endpoint Construction
    # Path: /runtimes/{EncodedArn}/invocations?qualifier=DEFAULT (for MCP)
    encoded_arn = quote(RUNTIME_ARN, safe='')
    invoke_url = f"https://bedrock-agentcore.{REGION}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
    print(f"{invoke_url=}")
    print("\nListing tools...")
    tools = list_tools(invoke_url)

    print("\nCalling tool: server_info...")
    result = call_tool(invoke_url, "server_info", {"session_id": session_id})

    print("\nCalling tool: 1 retrieve_memory...")
    result = call_tool(invoke_url, "retrieve_memory", {
        "query": "what are my food preferences",
        "max_results": 5,
        "actor_id": actor_id,
        "session_id": session_id,
    })



    print("\nCalling tool: 1 store_interaction...")
    result = call_tool(invoke_url,
                       "store_interaction",
                       {"user_msg": "Is sam a good dancer?",
                        "assistant_msg":"sam dances with heart...",
                        "actor_id":actor_id,
                        "session_id":session_id})

    
    print("\nCalling tool: 2 store_interaction...")
    result = call_tool(invoke_url,
                       "store_interaction",
                       {"user_msg": "where does sam dances?",
                        "assistant_msg":"sam dances at hotel california.",
                        "actor_id":actor_id,
                        "session_id":session_id})

    print("\nCalling tool: 2 retrieve_memory...")
    result = call_tool(invoke_url, "retrieve_memory", {
        "query": "what are my food preferences",
        "max_results": 5,
        "actor_id": actor_id,
        "session_id": session_id,
    })