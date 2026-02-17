"""
Author: Sarvagya Meel
Email: sarvagyameel2@gmail.com
Date: 11/02/26
"""

import os
import itertools
import json
from typing import Any, Dict, Optional
from pprint import pformat
import requests
import uuid
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
session_id  = str(uuid.uuid4())
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


def jsonrpc_local(url: str, method: str, params: Dict[str, Any], *, timeout_s: float = 60.0) -> Any:
    payload = {
        "jsonrpc": "2.0",
        "id": next(_id),
        "method": method,
        "params": params,
    }
    headers = {
        "content-type": "application/json",
        "accept": "application/vnd.mcp+json, application/json, text/event-stream",
    }
    r = requests.post(url, headers=headers, json=payload, timeout=timeout_s)
    print(r.status_code)
    r.raise_for_status()
    resp = pretty_print_mcp_from_r_text(r.text)

    if "error" in resp and resp["error"]:
        raise MCPError(f"JSON-RPC error: {resp['error']}")
    return resp.get("result")

def list_tools(url: str) -> Any:
    response =  jsonrpc_local(url, "tools/list", {})
    print_tools(response)
    return response

def call_tool(url: str, name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
    response = jsonrpc_local(url, "tools/call", {"name": name, "arguments": arguments or {}})
    print_tool_response(response)
    return response


if __name__ == "__main__":
    # 1. Configuration
    endpoint = "http://0.0.0.0:8000/mcp"

    print("\nListing tools...")
    result = list_tools(endpoint)

    print("\nCalling tool: server_info...")
    result = call_tool(endpoint, "server_info",
                       {"actor_id": actor_id,
                        "session_id": session_id})

    print("\nCalling tool: retrieve_memory...")
    result = call_tool(endpoint,
                       "retrieve_memory",
                       {"query":"what are my food preferences",
                        "max_results": 5,
                        "actor_id": actor_id,
                        "session_id": session_id})

    # print("\nCalling tool: store_interaction...")
    # result = call_tool(endpoint,
    #                    "store_interaction",
    #                    {"user_msg": "where does sam dances?",
    #                     "assistant_msg":"sam dances in california hotel",
    #                     "actor_id":actor_id,
    #                     "session_id":session_id})