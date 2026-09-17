# SEAM GitHub Intelligence Implementation

## Architecture
GitHub Intelligence is implemented as a reusable tool, not as a seventh agent.

Flow:

```text
Analysis Agent
-> GitHubIntelligenceTool decision
-> bounded static GitHub analysis when available/useful
-> structured findings in ProjectState
-> Planning/Coding/QA context
-> optional project artifacts
-> EventStore/WebSocket/UI messages
```

The six-agent architecture remains unchanged:

```text
Analysis -> Planning & Design -> Supervisor -> Coding -> QA -> Delivery
```

## Tool Interface
The tool lives at:

```text
SEAM/backend/tools/github_intelligence.py
```

Main methods:

- `should_research(state) -> bool`
- `research(state) -> dict`

The tool uses existing GitHub client/analyzer/ranker services under `backend/github`.

## Agent Integration
- Analysis Agent decides whether GitHub research is useful after structured requirements are produced.
- Planning Agent receives `state.github_findings.context` as static reference context.
- Coding Agent receives selected engineering patterns as context.
- QA Agent receives GitHub reference context but SEAM QA remains authoritative.

## Relevance Scoring
Existing ranking weights are preserved:

- Domain relevance: 20%
- Technology relevance: 20%
- Architecture relevance: 15%
- Testing relevance: 15%
- Security relevance: 10%
- Maintenance/activity: 10%
- Documentation: 5%
- License: 5%

## Security Boundaries
- GitHub token is read only from `GITHUB_TOKEN`.
- Token is never sent to the frontend.
- Token is never written into artifacts or events.
- Repositories are used only for bounded static analysis.
- Repository code is not executed.
- Source files are not copied automatically.
- GitHub is optional; missing token does not fail the workflow.

## Failure Handling
If GitHub is unavailable, missing a token, rate limited, or fails:

- SEAM emits a GitHub event.
- The workflow continues.
- Project status is not failed.
- Planning/Coding/QA receive no GitHub context.

Primary unavailable event:

```text
GITHUB_RESEARCH_UNAVAILABLE
```

## Event Flow
Implemented events:

- `GITHUB_SEARCH_STARTED`
- `GITHUB_SEARCH_COMPLETED`
- `GITHUB_REPOSITORY_SELECTED`
- `GITHUB_ANALYSIS_COMPLETED`
- `GITHUB_RESEARCH_UNAVAILABLE`
- `GITHUB_ANALYSIS_FAILED`

The UI conversation layer maps these events to GitHub Intelligence messages.

## Artifact Flow
When GitHub research is actually performed, SEAM writes and registers:

```text
generated_projects/<project>/analysis/github_intelligence.md
generated_projects/<project>/analysis/github_intelligence.json
```

These are registered through the existing Artifact Registry and appear in Explorer via the existing artifact/file events.

## RAG / Knowledge
GitHub findings are structured and can be converted into knowledge later, but SEAM does not automatically ingest every repository or source file into ChromaDB.

## Testing Results
Completed in this pass:

- Backend compile: PASS
- Frontend build: PASS
- Missing-token behavior: implemented as optional/unavailable path
- No new GitHub agent added
- Existing six-agent architecture preserved

Not completed in this pass:

- Live GitHub API validation with token
- Full workflow with GitHub available
- Full automated test suite for all GitHub API failure modes

## Operational Notes
To enable real GitHub research:

```powershell
$env:GITHUB_TOKEN="your_token"
```

Then start the backend normally. Without `GITHUB_TOKEN`, SEAM continues normally and reports GitHub Intelligence as unavailable.
