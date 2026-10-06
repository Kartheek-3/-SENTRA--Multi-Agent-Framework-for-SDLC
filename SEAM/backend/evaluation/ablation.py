from backend.events import event_bus


CAPABILITY_ALIASES = {
    "domain_rag": {"domain_rag", "domain-aware RAG", "DOMAIN_RAG"},
    "autonomous_repair": {"autonomous_repair", "autonomous repair", "AUTONOMOUS_REPAIR"},
    "contract_intelligence": {"contract_intelligence", "full-stack contract intelligence", "CONTRACT_INTELLIGENCE"},
    "runtime_validation": {"runtime_validation", "runtime validation", "RUNTIME_VALIDATION"},
    "github_intelligence": {"github_intelligence", "GitHub intelligence", "GITHUB_INTELLIGENCE"},
}


def capability_enabled(state, capability: str) -> bool:
    summary = getattr(state, "experiment_summary", None) or {}
    flags = summary.get("configuration_flags", {}) or {}
    if capability in flags:
        return bool(flags[capability])
    disabled = set(summary.get("disabled_capabilities", []) or [])
    aliases = CAPABILITY_ALIASES.get(capability, {capability})
    return not bool(disabled.intersection(aliases))


def mark_disabled(state, capability: str, agent: str, summary: str) -> None:
    event_bus.emit_sync("ABLATION_CAPABILITY_DISABLED", {
        "project_id": state.project_id,
        "agent": agent,
        "capability": capability,
        "status": "NOT_CONFIGURED",
        "summary": summary,
    })
