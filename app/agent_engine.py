import logging
import os
from deepagents import create_deep_agent
from langchain.agents.middleware import TodoListMiddleware
from langchain_ollama import ChatOllama
from app.config import OLLAMA_HOST, OLLAMA_MODEL, MCP_SERVER_URL
from app.mcp_client import load_mcp_tools
from app.prompts import load_system_prompt

logger = logging.getLogger("AgentEngine")

def init_deep_agent():
    """Initializes the Deep Agent harness with local Ollama, subagents, and memory."""
    logger.info(f"Initializing ChatOllama model '{OLLAMA_MODEL}' at '{OLLAMA_HOST}'...")
    
    # 1. Local LLM Provider
    llm = ChatOllama(
        base_url=OLLAMA_HOST,
        model=OLLAMA_MODEL,
        temperature=0.0
    )
    
    # 2. Dynamic Tool Discovery via MCP
    tools = load_mcp_tools(MCP_SERVER_URL)
    
    # 3. System Prompt & SOP Rules
    system_prompt = load_system_prompt()
    
    # 4. Memory Files
    memory_files = []
    agents_md = "/home/fayez/agent2/AGENTS.md"
    if os.path.exists(agents_md):
        memory_files.append(agents_md)
        
    # 5. Build Deep Agent
    logger.info("Building Deep Agent harness...")
    agent = create_deep_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        memory=memory_files if memory_files else None,
        middleware=[TodoListMiddleware()],
        subagents=[
            {
                "name": "rhel-diagnostics",
                "description": "Specialized subagent for executing pre-patch cluster checks and node health inspections",
                "system_prompt": (
                    "You are a specialized RHEL High Availability Cluster Diagnostic Subagent. "
                    "Run non-destructive checks (ansible_pcs_health_check, CIB status) and return a concise summary."
                )
            },
            {
                "name": "fleet-patcher",
                "description": "Specialized subagent for applying DNF updates and cluster node patching",
                "system_prompt": (
                    "You are a specialized RHEL Fleet Patching Subagent. "
                    "Coordinate node isolation, apply patch updates via Ansible, and verify service restoration."
                )
            }
        ]
    )
    logger.info("Deep Agent harness initialized successfully.")
    return agent
