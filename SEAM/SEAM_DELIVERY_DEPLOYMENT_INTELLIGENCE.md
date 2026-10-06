# SEAM Delivery & Deployment Intelligence

## Purpose

Delivery & Deployment Intelligence extends the existing DeliveryAgent. It does not add a DeploymentAgent and it does not replace Docker, runtime, contract, QA, repair, or tool systems.

The DeliveryAgent now aggregates existing evidence to answer:

- Is the release ready?
- Which deployment target is actually configured?
- Which artifacts and environment variables are required?
- Is packaging safe?
- Is post-deployment verification possible?
- Is rollback information available?

## State

ProjectState stores:

- `release_readiness`
- `deployment_profile`
- `deployment_artifacts`
- `deployment_result`
- `post_deployment_verification`
- `rollback_info`

Existing `delivery_result`, QA state, artifact registry entries, repair state, runtime state, and contract state remain authoritative.

## Release Readiness

`ReleaseReadiness` aggregates:

- QA result
- unresolved defects
- repair status
- targeted verification
- regression verification
- full-stack contract issues
- runtime contract results
- E2E results
- build/package evidence
- secret scan result
- documentation status

Statuses are:

- `READY`
- `NOT_READY`
- `BLOCKED`
- `NEEDS_REVIEW`

Delivery is blocked when blockers remain.

## Deployment Profile

`DeploymentProfile` is detected from real project files only.

Supported target detection:

- Docker when a Dockerfile exists
- Kubernetes when manifest files exist
- generic container deployment when compose files exist
- `NOT_CONFIGURED` when no deployment target is represented by artifacts

SEAM does not invent AWS, GCP, Azure, Cloud Run, Kubernetes, or Docker configuration.

## Environment Configuration

Environment requirements are detected from code and environment templates.

Only metadata is stored:

- name
- type
- required
- secret flag
- source

Secret values are never copied to state, logs, or artifacts.

## Secret Handling

Delivery scans generated project files for likely API keys, tokens, passwords, private keys, and credentialed connection strings.

Findings are represented as `SECRET_DETECTED` with file, line, category, and remediation. The secret value is not printed.

Placeholders such as `${DATABASE_URL}` are not treated as exposed secrets.

## Docker

Delivery reuses existing `docker_validate` and `docker_build` tools when a Dockerfile is present.

Dockerfile absence is reported as:

`containerization_status = NOT_CONFIGURED`

Delivery does not generate a Dockerfile unless a future policy explicitly routes that work through existing Coding/Delivery mechanisms.

## Artifacts

Delivery registers artifacts through the existing ArtifactRegistry and writes:

- `delivery/release_readiness.json`
- `delivery/deployment_profile.json`
- `delivery/deployment_result.json`
- `delivery/post_deployment_verification.json`
- `delivery/rollback_info.json`
- `delivery/release_readiness.md`
- existing delivery manifest, package, integrity, deployment, and README artifacts

## Git

Delivery captures local Git metadata when available:

- current branch
- current commit
- dirty status
- changed files

Delivery does not push, merge, force push, delete branches, or create GitHub releases.

## Post-Deployment Verification

`PostDeploymentVerification` reports:

- application health
- API health
- frontend availability
- contract verification
- E2E smoke status

It reuses existing runtime/contract/E2E evidence. If no reachable runtime is configured, the status is `NOT_CONFIGURED`.

## Rollback

`RollbackInfo` records rollback availability from real evidence such as Git commit and package artifact. It does not invent or execute rollback commands.

## Approval Boundary

Preparation may package, validate, and generate manifests.

Actual external deployment remains a high-risk action and must go through the existing approval/tooling model. SEAM does not silently deploy to external infrastructure.
