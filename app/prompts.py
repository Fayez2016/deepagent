import os

def load_system_prompt() -> str:
    """Aggregates system prompt rules from SOUL.md, AGENTS.md, and SOP documents."""
    prompt_parts = []
    
    # 1. Load Persona & Mindset (SOUL.md)
    soul_path = "/home/fayez/agent2/SOUL.md"
    if os.path.exists(soul_path):
        with open(soul_path, "r", encoding="utf-8") as f:
            prompt_parts.append(f"### SOUL & PERSONA DIRECTIVES:\n{f.read()}")
    else:
        prompt_parts.append(
            "### SOUL DIRECTIVE:\n"
            "You are a Senior Linux System Administrator and Site Reliability Engineer (SRE) specializing in "
            "Red Hat Enterprise Linux (RHEL) High Availability (HA) Pacemaker/Corosync clusters. "
            "Your mindset is recovery-first and action-oriented. Match hostnames strictly and literally."
        )
        
    # 2. Load Operating Procedures (SOP_RHEL_FLEET_PATCHING.md)
    sop_path = "/home/fayez/agent2/SOP_RHEL_FLEET_PATCHING.md"
    if os.path.exists(sop_path):
        with open(sop_path, "r", encoding="utf-8") as f:
            prompt_parts.append(f"### STANDARD OPERATING PROCEDURE (SOP):\n{f.read()}")
            
    # 3. Environment Directives
    prompt_parts.append(
        "### MANDATORY ENVIRONMENT RULES:\n"
        "- NO DIRECT SSH ACCESS: All operational and cluster actions MUST be performed via Ansible MCP tools.\n"
        "- LITERAL HOSTNAMES: Always pass hostnames exactly as provided (e.g. rhel-prod-01).\n"
        "- HIGH-RISK OPERATIONS: High-risk tools (reboot, node standby, VM reset) are gated by human operator approval."
    )

    return "\n\n".join(prompt_parts)
