import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Optional

from fastapi import APIRouter

from backend.performance import PERF_LOG


router = APIRouter(prefix="/api/performance", tags=["performance"])


@router.get("/summary")
def performance_summary(project_id: Optional[str] = None):
    events = []
    path = Path(PERF_LOG)
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if project_id and event.get("project_id") != project_id:
                    continue
                events.append(event)

    durations = defaultdict(list)
    failures = []
    for event in events:
        duration = event.get("duration_seconds")
        if duration is not None:
            durations[event.get("event_type", "unknown")].append(float(duration))
        if event.get("status") == "failure" or event.get("event_type", "").endswith("_failed"):
            failures.append(event)

    summary = {}
    for event_type, values in durations.items():
        ordered = sorted(values)
        p95_index = min(len(ordered) - 1, int(round((len(ordered) - 1) * 0.95)))
        summary[event_type] = {
            "count": len(values),
            "avg_seconds": round(mean(values), 3),
            "p95_seconds": round(ordered[p95_index], 3),
            "max_seconds": round(max(values), 3),
        }

    return {
        "project_id": project_id,
        "event_count": len(events),
        "durations": summary,
        "failure_count": len(failures),
        "recent_failures": failures[-10:],
    }
