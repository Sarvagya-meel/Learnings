"""
Author: Sarvagya Meel
Email: sarvagyameel2@gmail.com
Date: 11/02/26
"""

from __future__ import annotations

import os
import platform
import socket
import sys
import time
from typing import Any, Dict, Optional


def collect_server_info(*, mcp_host: str, mcp_port: int, service_name: str, tool_names: Optional[list[str]] = None) -> Dict[str, Any]:
    now = time.time()
    env_allowlist = [
        "MCP_HOST",
        "MCP_PORT",
        "LOG_LEVEL",
        "AGENTCORE_ACTOR_ID",
        "MEMORY_CONFIG_PATH",
        "AWS_REGION",
        "AWS_DEFAULT_REGION",
        "ECS_CONTAINER_METADATA_URI_V4",
        "HOSTNAME",
    ]

    info: Dict[str, Any] = {
        "service_name": service_name,
        "listen": {"host": mcp_host, "port": int(mcp_port)},
        "host": {
            "hostname": socket.gethostname(),
            "fqdn": socket.getfqdn(),
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "pid": os.getpid(),
        },
        "env": {k: os.getenv(k) for k in env_allowlist if os.getenv(k) is not None},
        "tools": tool_names or [],
        "collected_at_epoch": now,
    }
    return info
