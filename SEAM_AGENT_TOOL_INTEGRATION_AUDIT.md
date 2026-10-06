# SEAM Agent Tool Integration Audit

Date: 2026-09-20

| Agent | Existing Operation | Existing Service | Equivalent Tool | Should Use Tool? |
|---|---|---|---|---|
| Analysis | RAG retrieval | `KnowledgeService` | `rag_search` | YES |
| Analysis | GitHub intelligence | `GitHubIntelligenceTool` | `github_repository_context` / `github_freshness_check` | PARTIAL |
| Planning | RAG retrieval | `KnowledgeService` | `rag_search` | YES |
| Planning | diagram generation | existing diagram service | `mermaid_generate` | YES where appropriate |
| Coding | RAG retrieval | `KnowledgeService` | `rag_search` | YES |
| Coding | filesystem write | direct filesystem + ArtifactRegistry | `file_write` | YES |
| Coding | Git inspection/versioning | none/direct git need | `git_status` / `git_diff` / `git_add` / `git_commit` | YES |
| QA | RAG retrieval | `KnowledgeService` | `rag_search` | YES |
| QA | pytest | deterministic QA path | `pytest_runner` | YES |
| QA | API testing | none | `api_test_runner` | YES where applicable |
| Delivery | Docker | none | `docker_validate` / `docker_build` | YES |
| Supervisor | state routing | internal orchestration | none | NO |

## Findings

Before this integration pass, agents called RAG, diagram generation, filesystem writes, QA checks, and delivery services directly. The ToolRegistry and ToolExecutor existed and were covered by focused tests, but the LangGraph agents did not invoke the registry/executor path.

## Integration Decision

A small bridge was added in `backend/tools/agent_tools.py`. It keeps the existing registry, permission engine, executor, EventStore events, and ProjectState. Agents call this bridge only for operations that already have registered tools.

