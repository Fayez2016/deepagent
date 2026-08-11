import os
import json
import asyncio
import inspect
import logging
import requests
from typing import List, Any
from langchain_core.tools import StructuredTool
from app.config import MCP_SERVER_URL

logger = logging.getLogger("MCPClient")

def load_mcp_config() -> str:
    """Discovers MCP server URL from .mcp.json or returns default MCP_SERVER_URL."""
    mcp_config_path = "/app/.mcp.json" if os.path.exists("/app/.mcp.json") else ".mcp.json"
    if os.path.exists(mcp_config_path):
        try:
            with open(mcp_config_path, "r") as f:
                data = json.load(f)
                servers = data.get("mcpServers", {})
                if "ansible-mcp" in servers:
                    url = servers["ansible-mcp"].get("url")
                    if url:
                        logger.info(f"Discovered MCP URL '{url}' from .mcp.json config.")
                        return url
        except Exception as e:
            logger.warning(f"Error reading .mcp.json: {e}")
    return MCP_SERVER_URL

def _call_mcp_tool(tool_name: str, **kwargs):
    """Executes a tool call against the Ansible MCP server."""
    try:
        url = f"http://ansible-mcp:8000/tools/{tool_name}"
        resp = requests.post(url, json=kwargs, timeout=120)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("result", str(data))
        return f"MCP Tool Error ({resp.status_code}): {resp.text}"
    except Exception as e:
        return f"MCP Tool Exception: {str(e)}"

def create_ansible_tool(name: str, description: str):
    """Creates a LangChain StructuredTool dynamically for Ansible MCP tools."""
    return StructuredTool.from_function(
        func=lambda **kwargs: _call_mcp_tool(name, **kwargs),
        name=name,
        description=description
    )

def load_mcp_tools(server_url: str = None) -> List[Any]:
    """Connects to the Ansible MCP server via HTTP and loads LangChain compatible tool definitions."""
    if not server_url:
        server_url = load_mcp_config()
        
    tools = []
    try:
        from langchain_mcp_adapters.tools import load_mcp_tools as mcp_loader
        logger.info(f"Connecting to Ansible MCP Server at {server_url}...")
        
        res = mcp_loader(server_url)
        if inspect.isawaitable(res):
            tools = asyncio.run(res)
        else:
            tools = res
        logger.info(f"Loaded {len(tools)} tools from MCP server.")
        if tools:
            return tools
    except Exception as e:
        logger.warning(f"langchain_mcp_adapters loader fallback: {e}")

    # Fallback to direct tool registration
    logger.info("Registering Ansible MCP tools...")
    tool_specs = [
        ("ansible_pcs_health_check", "Comprehensive RHEL HA cluster health and quorum diagnostic check."),
        ("ansible_reboot_host", "Reboots a single target host node (Requires HITL approval)."),
        ("ansible_reboot_fleet", "Reboots the entire cluster fleet (Requires HITL approval)."),
        ("ansible_pcs_node_standby", "Places a cluster node into standby mode (Requires HITL approval)."),
        ("ansible_pcs_node_unstandby", "Takes a cluster node out of standby mode and restores services."),
        ("ansible_pcs_maintenance_mode", "Enables or disables global cluster maintenance mode (Requires HITL approval)."),
        ("ansible_install_package", "Installs or updates a DNF/YUM package on target host."),
        ("ansible_patch_fleet", "Executes fleet security patching playbook."),
        ("ansible_expand_fs", "Expands LVM / XFS filesystem volume on target host."),
        ("ansible_vmware_reset", "Performs hard VM reset via VMware API (Requires HITL approval)."),
        ("ansible_send_email", "Sends email notification.")
    ]

    for name, desc in tool_specs:
        tools.append(create_ansible_tool(name, desc))

    return tools
