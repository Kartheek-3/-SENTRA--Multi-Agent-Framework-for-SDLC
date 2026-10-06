import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from typing import Iterable, Optional

from backend.events import event_bus
from backend.tools.errors import ToolPermissionError
from backend.tools.permissions import PermissionEngine
from backend.tools.registry import ToolRegistry, default_registry
from backend.tools.schemas import ToolErrorModel, ToolExecutionContext, ToolRequest, ToolResult, redact_secret


class ToolExecutor:
    def __init__(self, registry: ToolRegistry = default_registry, permission_engine: Optional[PermissionEngine] = None):
        self.registry = registry
        self.permission_engine = permission_engine or PermissionEngine(registry)

    def execute_dict(self, payload: dict) -> ToolResult:
        return self.execute(ToolRequest.model_validate(payload))

    def execute(self, request: ToolRequest, project_root: Optional[str] = None, paths: Optional[Iterable[str]] = None) -> ToolResult:
        started = time.perf_counter()
        event_base = {
            "project_id": request.project_id,
            "task_id": request.task_id,
            "agent": request.agent_name,
            "tool_name": request.tool_name,
            "execution_id": request.execution_id,
        }
        event_bus.emit_sync("TOOL_REQUESTED", {**event_base, "status": "requested"})
        tool = self.registry.get(request.tool_name)
        context = ToolExecutionContext(
            project_id=request.project_id,
            agent_name=request.agent_name,
            task_id=request.task_id,
            project_root=project_root,
            approved=request.approved,
        )
        try:
            permission = self.permission_engine.check(tool.name, context, paths=paths)
            event_bus.emit_sync("TOOL_PERMISSION_CHECKED", {**event_base, "allowed": permission.allowed, "requires_approval": permission.requires_approval})
            if not permission.allowed:
                event_bus.emit_sync("TOOL_PERMISSION_DENIED", {**event_base, "status": "denied", "reason": permission.reason})
                return self._failure(tool.name, request.execution_id, "PERMISSION_DENIED", permission.reason, started)

            tool_input = tool.validate_input(redact_secret(request.input))
            event_bus.emit_sync("TOOL_STARTED", {**event_base, "status": "running"})
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(tool.execute, tool_input, context)
                result = future.result(timeout=tool.timeout)
            result.execution_id = request.execution_id
            result.duration_ms = int((time.perf_counter() - started) * 1000)
            result.structured_data = redact_secret(result.structured_data)
            event_bus.emit_sync("TOOL_COMPLETED", {**event_base, "status": "completed", "duration_ms": result.duration_ms})
            return result
        except FutureTimeout:
            event_bus.emit_sync("TOOL_TIMEOUT", {**event_base, "status": "timeout"})
            return self._failure(tool.name, request.execution_id, "TIMEOUT", "Tool execution timed out", started)
        except ToolPermissionError as exc:
            event_bus.emit_sync("TOOL_PERMISSION_DENIED", {**event_base, "status": "denied", "reason": str(exc)})
            return self._failure(tool.name, request.execution_id, "PERMISSION_DENIED", str(exc), started)
        except Exception as exc:
            event_bus.emit_sync("TOOL_FAILED", {**event_base, "status": "failed", "error": str(exc)})
            return self._failure(tool.name, request.execution_id, "FAILED", str(exc), started)

    def _failure(self, tool_name: str, execution_id: str, code: str, message: str, started: float) -> ToolResult:
        return ToolResult(
            success=False,
            tool_name=tool_name,
            execution_id=execution_id,
            duration_ms=int((time.perf_counter() - started) * 1000),
            error=ToolErrorModel(code=code, message=message),
        )
