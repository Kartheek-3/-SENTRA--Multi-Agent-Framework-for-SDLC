import json
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Optional


RUNTIME_DIR = Path(__file__).resolve().parents[2] / ".seam" / "runtime"
PERF_LOG = RUNTIME_DIR / "performance_events.jsonl"


class PerformanceRecorder:
    def __init__(self):
        self._lock = RLock()
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

    def record(self, event_type: str, **payload: Any) -> Dict[str, Any]:
        event = {
            "performance_event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": time.time(),
            **payload,
        }
        with self._lock:
            with PERF_LOG.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, default=str) + "\n")
        return event

    @contextmanager
    def span(self, event_type: str, **payload: Any):
        start = time.perf_counter()
        start_wall = time.time()
        self.record(f"{event_type}_started", start_time=start_wall, **payload)
        try:
            yield
            status = "success"
            error = None
        except Exception as exc:
            status = "failure"
            error = str(exc)
            raise
        finally:
            end_wall = time.time()
            data = {
                "start_time": start_wall,
                "end_time": end_wall,
                "duration_seconds": time.perf_counter() - start,
                "status": status,
                **payload,
            }
            if error:
                data["error"] = error
            self.record(f"{event_type}_completed", **data)


performance_recorder = PerformanceRecorder()


def timed_call(event_type: str, func, *, project_id: Optional[str] = None, **payload: Any):
    with performance_recorder.span(event_type, project_id=project_id, **payload):
        return func()


def timed_llm_call(func, *, project_id: Optional[str] = None, **payload: Any):
    from backend.concurrency import llm_semaphore

    with llm_semaphore:
        return timed_call("llm_call", func, project_id=project_id, **payload)


def estimate_tokens(text: Any) -> int:
    if text is None:
        return 0
    value = text if isinstance(text, str) else json.dumps(text, default=str)
    return max(1, len(value) // 4)
