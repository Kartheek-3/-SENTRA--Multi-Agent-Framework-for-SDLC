# SEAM Agent Tool Matrix

Date: 2026-09-19

| Agent | Tools |
|---|---|
| AnalysisAgent | `rag_search`, `github_repository_context`, `github_freshness_check`, `file_read`, `file_search`, `git_status`, `git_log`, `git_diff` |
| PlanningAgent | `rag_search`, `github_repository_context`, `file_read`, `file_search`, `mermaid_generate`, `api_spec_validate`, `git_status`, `git_log`, `git_diff`, `detect_frontend_capabilities` |
| SupervisorAgent | `github_freshness_check`, `github_repository_context`, `github_compare_commits`, `git_status`, `git_diff`, `git_log`, `git_branch` |
| CodingAgent | `rag_search`, `github_repository_context`, `file_read`, `file_search`, `file_write`, `git_status`, `git_diff`, `git_log`, `git_branch`, `git_create_branch`, `git_checkout`, `git_add`, `git_commit`, `git_stash`, `git_merge`, `git_push`, `detect_frontend_capabilities`, `npm_runner`, `typecheck_runner`, `lint_runner`, `build_runner` |
| QAAgent | `rag_search`, `github_repository_context`, `file_read`, `file_search`, `git_status`, `git_diff`, `git_log`, `git_branch`, `pytest_runner`, `api_test_runner`, `runtime_manager`, `runtime_api_validator`, `api_spec_validate`, `detect_frontend_capabilities`, `npm_runner`, `typecheck_runner`, `lint_runner`, `frontend_test_runner`, `playwright_runner`, `build_runner`, `browser_screenshot`, `accessibility_checker` |
| DeliveryAgent | `rag_search`, `file_read`, `file_search`, `git_status`, `git_diff`, `git_log`, `git_branch`, `git_commit`, `git_merge`, `git_push`, `docker_validate`, `docker_build`, `build_runner` |

High-risk filesystem delete, `git_merge`, `git_push`, and Docker build remain approval-gated. Git push rejects force/destructive options and does not alter remotes.

Frontend tooling remains inside the SEAM ToolRegistry and PermissionEngine. n8n is not used for internal frontend execution, and MCP remains an external integration boundary.

Frontend architecture planning is part of PlanningAgent. It uses `detect_frontend_capabilities`, RAG context, Analysis output, and `SystemDesign.api_endpoints` to populate `ProjectState.frontend_architecture_plan`. CodingAgent and QAAgent consume that plan; no FrontendAgent was added.

Full-stack contract intelligence is also part of PlanningAgent and QAAgent. It builds `ProjectState.full_stack_contract` from the frontend architecture plan, API endpoints, and database schema, then exposes concrete `contract_issues` for CodingAgent rework. No ContractAgent was added.

Runtime contract validation is a QAAgent tool capability through `runtime_api_validator`. It only runs against local `ProjectState.runtime_base_url`, either explicitly configured or populated by `runtime_manager`.

Runtime lifecycle management is a QAAgent tool capability through `runtime_manager`. It detects supported project runtimes, starts project-owned localhost processes, performs health checks, populates `ProjectState.runtime_base_url`, and stops only SEAM-owned processes.

Application-level E2E validation is part of QAAgent. It generates `e2e_scenarios`, executes configured Playwright/browser tooling through existing tools, stores `e2e_results`, and records evidence-based `defect_locations`. No E2EAgent was added.

Autonomous defect repair is handled by Supervisor, CodingAgent, and QAAgent using existing tools. QA creates `repair_plans`, Supervisor routes bounded rework, Coding records `repair_results`, and QA records targeted/regression verification. No RepairAgent was added.

Delivery & Deployment Intelligence is handled by the existing DeliveryAgent. It aggregates QA, contracts, runtime, E2E, repair, Git, Docker, artifact, documentation, and secret-scan evidence into `release_readiness`, `deployment_profile`, `deployment_artifacts`, `deployment_result`, `post_deployment_verification`, and `rollback_info`. It prepares and packages artifacts but does not perform external deployment, push, merge, or release creation without the existing approval/tool model. No DeploymentAgent was added.
