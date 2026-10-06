import os
import subprocess

from backend.tools.executor import ToolExecutor
from backend.models.state import ProjectState
from backend.tools.frontend.tools import detect_frontend_capabilities, detect_frontend_project
from backend.tools.registry import default_registry
from backend.tools.schemas import ToolRequest


def _write_package(root, scripts=None, deps=None):
    scripts = scripts or {}
    deps = deps or {}
    content = {
        "scripts": scripts,
        "dependencies": deps,
        "devDependencies": deps,
    }
    (root / "package.json").write_text(__import__("json").dumps(content), encoding="utf-8")


def _execute(tool_name, tmp_path, payload=None, agent="QAAgent"):
    return ToolExecutor(default_registry).execute_dict(
        {
            "tool_name": tool_name,
            "agent_name": agent,
            "project_id": "p",
            "input": payload or {"project_root": "."},
        },
    )


def test_frontend_tools_are_registered():
    for name in [
        "npm_runner",
        "typecheck_runner",
        "lint_runner",
        "frontend_test_runner",
        "playwright_runner",
        "build_runner",
        "browser_screenshot",
        "accessibility_checker",
        "detect_frontend_capabilities",
    ]:
        assert default_registry.is_registered(name)


def test_npm_runner_rejects_arbitrary_script(tmp_path):
    _write_package(tmp_path, scripts={"build": "vite build"})
    result = ToolExecutor(default_registry).execute(
        __import__("backend.tools.schemas", fromlist=["ToolRequest"]).ToolRequest(
            tool_name="npm_runner",
            agent_name="CodingAgent",
            project_id="p",
            input={"project_root": ".", "operation": "script", "script": "postinstall"},
        ),
        project_root=str(tmp_path),
    )

    assert result.success is False
    assert result.error.code == "FAILED"


def test_build_runner_uses_existing_build_script(monkeypatch, tmp_path):
    _write_package(tmp_path, scripts={"build": "vite build"})
    calls = []

    def fake_run(command, cwd, capture_output, text, timeout):
        calls.append((command, cwd, timeout))
        return subprocess.CompletedProcess(command, 0, stdout="built", stderr="")

    monkeypatch.setattr("backend.tools.frontend.tools.subprocess.run", fake_run)

    result = ToolExecutor(default_registry).execute(
        __import__("backend.tools.schemas", fromlist=["ToolRequest"]).ToolRequest(
            tool_name="build_runner",
            agent_name="QAAgent",
            project_id="p",
            input={"project_root": "."},
        ),
        project_root=str(tmp_path),
    )

    assert result.success is True
    assert calls[0][0][-2:] == ["run", "build"]


def test_frontend_test_runner_not_configured_without_framework(tmp_path):
    _write_package(tmp_path, scripts={"build": "vite build"})

    result = ToolExecutor(default_registry).execute(
        __import__("backend.tools.schemas", fromlist=["ToolRequest"]).ToolRequest(
            tool_name="frontend_test_runner",
            agent_name="QAAgent",
            project_id="p",
            input={"project_root": "."},
        ),
        project_root=str(tmp_path),
    )

    assert result.success is False
    assert result.structured_data["status"] == "NOT_CONFIGURED"


def test_typecheck_runner_not_configured_without_script_or_local_tsc(tmp_path):
    _write_package(tmp_path)
    (tmp_path / "tsconfig.json").write_text("{}", encoding="utf-8")

    result = ToolExecutor(default_registry).execute(
        __import__("backend.tools.schemas", fromlist=["ToolRequest"]).ToolRequest(
            tool_name="typecheck_runner",
            agent_name="QAAgent",
            project_id="p",
            input={"project_root": "."},
        ),
        project_root=str(tmp_path),
    )

    assert result.structured_data["status"] == "NOT_CONFIGURED"


def test_frontend_tool_path_traversal_denied(tmp_path):
    result = ToolExecutor(default_registry).execute(
        __import__("backend.tools.schemas", fromlist=["ToolRequest"]).ToolRequest(
            tool_name="build_runner",
            agent_name="QAAgent",
            project_id="p",
            input={"project_root": ".."},
        ),
        project_root=str(tmp_path),
    )

    assert result.success is False
    assert result.error.code == "PERMISSION_DENIED"


def test_frontend_output_redacts_secrets(monkeypatch, tmp_path):
    _write_package(tmp_path, scripts={"build": "vite build"})

    def fake_run(command, cwd, capture_output, text, timeout):
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="token=abc123")

    monkeypatch.setattr("backend.tools.frontend.tools.subprocess.run", fake_run)

    result = ToolExecutor(default_registry).execute(
        __import__("backend.tools.schemas", fromlist=["ToolRequest"]).ToolRequest(
            tool_name="build_runner",
            agent_name="QAAgent",
            project_id="p",
            input={"project_root": "."},
        ),
        project_root=str(tmp_path),
    )

    assert "[REDACTED]" in result.stderr
    assert "abc123" not in result.stderr


def test_detect_frontend_project(tmp_path):
    _write_package(tmp_path, scripts={"build": "vite build"}, deps={"react": "latest", "vite": "latest"})
    (tmp_path / "src").mkdir()
    (tmp_path / "tsconfig.json").write_text("{}", encoding="utf-8")

    detected = detect_frontend_project(str(tmp_path))

    assert detected["package_detected"] is True
    assert "react" in detected["frameworks"]
    assert detected["typescript"] is True
    assert detected["has_src"] is True


def test_detect_frontend_capabilities_react_vite_typescript_vitest(tmp_path):
    _write_package(
        tmp_path,
        scripts={
            "dev": "vite",
            "build": "vite build",
            "lint": "eslint .",
            "typecheck": "tsc --noEmit",
            "test": "vitest",
        },
        deps={"react": "latest", "vite": "latest", "typescript": "latest", "vitest": "latest"},
    )
    (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")
    (tmp_path / "tsconfig.json").write_text("{}", encoding="utf-8")
    (tmp_path / "vite.config.ts").write_text("export default {}", encoding="utf-8")
    (tmp_path / "vitest.config.ts").write_text("export default {}", encoding="utf-8")

    profile = detect_frontend_capabilities(str(tmp_path))

    assert profile.framework == "react"
    assert profile.language == "typescript"
    assert profile.build_system == "vite"
    assert profile.package_manager == "npm"
    assert profile.typecheck_available is True
    assert profile.lint_available is True
    assert profile.frontend_test_framework == "vitest"
    assert profile.build_output_directory == "dist"
    assert profile.build_command[-2:] == ["run", "build"]


def test_detect_frontend_capabilities_next_output(tmp_path):
    _write_package(tmp_path, scripts={"dev": "next dev", "build": "next build"}, deps={"next": "latest", "react": "latest"})
    (tmp_path / "next.config.js").write_text("module.exports = {}", encoding="utf-8")

    profile = detect_frontend_capabilities(str(tmp_path))

    assert profile.framework == "next"
    assert profile.build_system == "next"
    assert profile.build_output_directory == ".next"


def test_detect_package_manager_lock_files(tmp_path):
    _write_package(tmp_path)
    (tmp_path / "pnpm-lock.yaml").write_text("", encoding="utf-8")

    profile = detect_frontend_capabilities(str(tmp_path))

    assert profile.package_manager == "pnpm"


def test_unknown_framework_is_not_guessed(tmp_path):
    _write_package(tmp_path, scripts={"build": "custom build"}, deps={"some-ui": "1.0.0"})

    profile = detect_frontend_capabilities(str(tmp_path))

    assert profile.framework == "UNKNOWN"
    assert profile.build_system == "UNKNOWN"


def test_detection_tool_emits_events(monkeypatch, tmp_path):
    _write_package(tmp_path, scripts={"build": "vite build"}, deps={"react": "latest", "vite": "latest"})
    emitted = []
    monkeypatch.setattr("backend.tools.frontend.tools.event_bus.emit_sync", lambda event, payload: emitted.append(event))

    result = ToolExecutor(default_registry).execute(
        ToolRequest(
            tool_name="detect_frontend_capabilities",
            agent_name="QAAgent",
            project_id="p",
            input={"project_root": "."},
        ),
        project_root=str(tmp_path),
    )

    assert result.success is True
    assert result.structured_data["framework"] == "react"
    assert "FRONTEND_DETECTION_STARTED" in emitted
    assert "FRONTEND_CAPABILITIES_DETECTED" in emitted


def test_detection_through_agent_bridge_updates_state(tmp_path, monkeypatch):
    from backend.tools.agent_tools import AgentToolContext

    _write_package(tmp_path, scripts={"build": "vite build"}, deps={"react": "latest", "vite": "latest"})
    state = ProjectState(project_id="p", domain="frontend_test")
    monkeypatch.setattr(AgentToolContext, "project_root", property(lambda self: str(tmp_path)))
    context = AgentToolContext(state, "QAAgent", task_id="TASK-1")

    result = context.run("detect_frontend_capabilities", {"project_root": "."})

    assert result.success is True
    assert result.structured_data["framework"] == "react"
    assert state.execution_history[-1]["tool_name"] == "detect_frontend_capabilities"
