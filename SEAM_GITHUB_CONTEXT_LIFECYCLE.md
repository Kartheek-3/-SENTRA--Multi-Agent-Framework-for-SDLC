# SEAM GitHub Context Lifecycle

## Normal Flow

```text
NEW
  -> FULL ANALYSIS
  -> CURRENT
  -> CHANGE DETECTED
  -> INCREMENTAL UPDATE
  -> CURRENT
```

## Failure / Recovery Flow

```text
CURRENT
  -> API FAILURE
  -> STALE
  -> REFRESH
  -> CURRENT
```

## Context Contract

Every repository context supplied to agents must include:

```json
{
  "repository": "owner/project",
  "commit_sha": "abc123",
  "analysis_version": 4,
  "status": "CURRENT",
  "last_analyzed_at": "2026-09-19T00:00:00+00:00"
}
```

If GitHub is unavailable, agents receive `STALE` or `UNAVAILABLE`; SEAM must not silently present stale repository intelligence as current.
