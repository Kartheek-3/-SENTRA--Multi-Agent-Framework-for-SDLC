from backend.tools.registry import default_registry


def test_agent_tool_matrix_contains_phase1_assignments():
    analysis_tools = {tool.name for tool in default_registry.get_agent_tools("AnalysisAgent")}
    planning_tools = {tool.name for tool in default_registry.get_agent_tools("PlanningAgent")}
    supervisor_tools = {tool.name for tool in default_registry.get_agent_tools("SupervisorAgent")}
    coding_tools = {tool.name for tool in default_registry.get_agent_tools("CodingAgent")}
    qa_tools = {tool.name for tool in default_registry.get_agent_tools("QAAgent")}
    delivery_tools = {tool.name for tool in default_registry.get_agent_tools("DeliveryAgent")}

    read_only_git = {"git_status", "git_diff", "git_log", "git_branch"}
    assert {"rag_search", "github_repository_context", "file_read", "file_search", "git_status", "git_diff", "git_log"}.issubset(analysis_tools)
    assert {"git_status", "git_diff", "git_log"}.issubset(planning_tools)
    assert read_only_git.issubset(supervisor_tools)
    assert {
        "file_write",
        "git_status",
        "git_diff",
        "git_log",
        "git_branch",
        "git_create_branch",
        "git_checkout",
        "git_add",
        "git_commit",
        "git_stash",
        "git_merge",
        "git_push",
    }.issubset(coding_tools)
    assert {"pytest_runner", "api_test_runner", "api_spec_validate", "git_status", "git_diff", "git_log", "git_branch"}.issubset(qa_tools)
    assert {"git_status", "git_diff", "git_log", "git_branch", "git_commit", "git_merge", "git_push"}.issubset(delivery_tools)
