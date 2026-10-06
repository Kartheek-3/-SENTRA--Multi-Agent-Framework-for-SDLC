import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from backend.events import event_bus
from backend.tools.base import SEAMTool
from backend.tools.permissions import PermissionEngine
from backend.tools.registry import default_registry
from backend.tools.schemas import RiskLevel, ToolExecutionContext, ToolResult


FRONTEND_SOURCE_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".css", ".scss", ".html"}
SAFE_NPM_OPERATIONS = {"install", "ci", "script"}
SAFE_NPM_SCRIPTS = {"dev", "build", "preview", "lint", "typecheck", "test"}
DETECTION_FILES = [
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "tsconfig.json",
    "vite.config.ts",
    "vite.config.js",
    "next.config.ts",
    "next.config.js",
    "angular.json",
    "eslint.config.js",
    "eslint.config.mjs",
    ".eslintrc",
    ".eslintrc.json",
    ".eslintrc.js",
    "vitest.config.ts",
    "vitest.config.js",
    "jest.config.ts",
    "jest.config.js",
    "playwright.config.ts",
    "playwright.config.js",
]


class FrontendProjectInput(BaseModel):
    project_root: str = "."


class NPMRunnerInput(BaseModel):
    project_root: str = "."
    operation: str = "script"
    script: Optional[str] = None


class BrowserStep(BaseModel):
    action: str
    selector: Optional[str] = None
    value: Optional[str] = None
    text: Optional[str] = None


class PlaywrightInput(BaseModel):
    project_root: str = "."
    url: Optional[str] = None
    steps: List[BrowserStep] = Field(default_factory=list)


class BrowserScreenshotInput(BaseModel):
    project_root: str = "."
    url: str
    filename: str = "frontend_screenshot.png"


class FrontendCapabilityProfile(BaseModel):
    package_json: bool = False
    framework: str = "UNKNOWN"
    language: str = "UNKNOWN"
    package_manager: str = "UNKNOWN"
    build_system: str = "UNKNOWN"
    available_scripts: List[str] = Field(default_factory=list)
    typecheck_available: bool = False
    lint_available: bool = False
    frontend_test_framework: str = "not_configured"
    playwright_available: bool = False
    accessibility_available: bool = False
    dev_server_available: bool = False
    build_available: bool = False
    dev_server_command: Optional[List[str]] = None
    build_command: Optional[List[str]] = None
    test_command: Optional[List[str]] = None
    lint_command: Optional[List[str]] = None
    typecheck_command: Optional[List[str]] = None
    build_output_directory: Optional[str] = None
    detected_files: List[str] = Field(default_factory=list)

    @field_validator(
        "dev_server_command",
        "build_command",
        "test_command",
        "lint_command",
        "typecheck_command",
    )
    @classmethod
    def commands_are_structured(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return value
        if not value or any(not part or any(ch in part for ch in [";", "&", "|", "\n", "\r"]) for part in value):
            raise ValueError("commands must be structured argument arrays")
        return value


def _safe_root(project_root: str, context: ToolExecutionContext) -> str:
    return PermissionEngine(default_registry).ensure_safe_path(project_root, context.project_root)


def _load_package_json(root: str) -> Dict[str, Any]:
    package_path = os.path.join(root, "package.json")
    if not os.path.exists(package_path):
        return {}
    with open(package_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _detect_package_manager(root: str) -> str:
    if os.path.exists(os.path.join(root, "package-lock.json")):
        return "npm"
    if os.path.exists(os.path.join(root, "pnpm-lock.yaml")):
        return "pnpm"
    if os.path.exists(os.path.join(root, "yarn.lock")):
        return "yarn"
    return "npm"


def _script_exists(root: str, script: str) -> bool:
    package_json = _load_package_json(root)
    return script in (package_json.get("scripts") or {})


def _has_dependency(root: str, names: List[str]) -> bool:
    package_json = _load_package_json(root)
    deps = {}
    deps.update(package_json.get("dependencies") or {})
    deps.update(package_json.get("devDependencies") or {})
    return any(name in deps for name in names)


def _dependencies(root: str) -> Dict[str, str]:
    package_json = _load_package_json(root)
    deps = {}
    deps.update(package_json.get("dependencies") or {})
    deps.update(package_json.get("devDependencies") or {})
    return deps


def _run(command: List[str], cwd: str, timeout: int) -> ToolResult:
    started = time.perf_counter()
    proc = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return ToolResult(
        success=proc.returncode == 0,
        tool_name="",
        stdout=proc.stdout,
        stderr=proc.stderr,
        duration_ms=int((time.perf_counter() - started) * 1000),
        structured_data={
            "command": command,
            "exit_code": proc.returncode,
            "status": "SUCCESS" if proc.returncode == 0 else "FAILED",
        },
    )


def _not_configured(tool_name: str, reason: str) -> ToolResult:
    return ToolResult(
        success=False,
        tool_name=tool_name,
        structured_data={"status": "NOT_CONFIGURED", "reason": reason},
        stderr=reason,
    )


def _build_script_command(root: str, script: str) -> List[str]:
    manager = _detect_package_manager(root)
    if manager == "yarn":
        return ["yarn", script]
    if manager == "pnpm":
        return ["pnpm", "run", script]
    return ["npm.cmd" if os.name == "nt" else "npm", "run", script]


def _script_command_if_present(root: str, script: str) -> Optional[List[str]]:
    return _build_script_command(root, script) if _script_exists(root, script) else None


def _local_bin(root: str, executable: str) -> Optional[str]:
    suffix = ".cmd" if os.name == "nt" else ""
    candidate = os.path.join(root, "node_modules", ".bin", f"{executable}{suffix}")
    return candidate if os.path.exists(candidate) else None


class NPMRunnerTool(SEAMTool):
    name = "npm_runner"
    description = "Run controlled npm/package-manager operations inside a frontend project."
    category = "frontend"
    input_schema = NPMRunnerInput
    allowed_agents = ["CodingAgent", "QAAgent"]
    risk_level = RiskLevel.MEDIUM
    timeout = 180

    def execute(self, tool_input: NPMRunnerInput, context: ToolExecutionContext) -> ToolResult:
        root = _safe_root(tool_input.project_root, context)
        if not os.path.exists(os.path.join(root, "package.json")):
            return _not_configured(self.name, "package.json not found")
        operation = tool_input.operation
        if operation not in SAFE_NPM_OPERATIONS:
            raise ValueError("Unsupported npm operation")
        npm = "npm.cmd" if os.name == "nt" else "npm"
        if operation == "install":
            command = [npm, "install"]
        elif operation == "ci":
            command = [npm, "ci"]
        else:
            script = tool_input.script or ""
            if script not in SAFE_NPM_SCRIPTS:
                raise ValueError("Unsupported npm script")
            if not _script_exists(root, script):
                return _not_configured(self.name, f"npm script not configured: {script}")
            command = _build_script_command(root, script)
        result = _run(command, root, self.timeout)
        result.tool_name = self.name
        result.structured_data.update({"operation": operation, "script": tool_input.script, "package_manager": _detect_package_manager(root)})
        return result


class FrontendCapabilityDetectionTool(SEAMTool):
    name = "detect_frontend_capabilities"
    description = "Detect frontend framework, scripts, package manager, validation tooling, and build output without executing project code."
    category = "frontend"
    input_schema = FrontendProjectInput
    allowed_agents = ["CodingAgent", "QAAgent", "PlanningAgent"]
    risk_level = RiskLevel.READ_ONLY

    def execute(self, tool_input: FrontendProjectInput, context: ToolExecutionContext) -> ToolResult:
        root = _safe_root(tool_input.project_root, context)
        event_bus.emit_sync("FRONTEND_DETECTION_STARTED", {
            "project_id": context.project_id,
            "agent": context.agent_name,
            "task_id": context.task_id,
            "summary": "Frontend capability detection started.",
        })
        try:
            profile = detect_frontend_capabilities(root)
            event_bus.emit_sync("FRONTEND_CAPABILITIES_DETECTED", {
                "project_id": context.project_id,
                "agent": context.agent_name,
                "task_id": context.task_id,
                "summary": f"Frontend detected: {profile.framework} / {profile.language} / {profile.build_system}",
                "framework": profile.framework,
                "language": profile.language,
                "build_system": profile.build_system,
                "package_manager": profile.package_manager,
            })
            return ToolResult(
                success=True,
                tool_name=self.name,
                structured_data=profile.model_dump(),
            )
        except Exception as exc:
            event_bus.emit_sync("FRONTEND_DETECTION_FAILED", {
                "project_id": context.project_id,
                "agent": context.agent_name,
                "task_id": context.task_id,
                "error": str(exc),
                "summary": "Frontend capability detection failed.",
            })
            raise


class TypecheckRunnerTool(SEAMTool):
    name = "typecheck_runner"
    description = "Run configured frontend TypeScript type checking."
    category = "frontend"
    input_schema = FrontendProjectInput
    allowed_agents = ["CodingAgent", "QAAgent"]
    risk_level = RiskLevel.MEDIUM
    timeout = 180

    def execute(self, tool_input: FrontendProjectInput, context: ToolExecutionContext) -> ToolResult:
        root = _safe_root(tool_input.project_root, context)
        if _script_exists(root, "typecheck"):
            command = _build_script_command(root, "typecheck")
        elif os.path.exists(os.path.join(root, "tsconfig.json")) and _local_bin(root, "tsc"):
            command = [_local_bin(root, "tsc"), "--noEmit"]
        else:
            return _not_configured(self.name, "No typecheck script or local TypeScript compiler found")
        result = _run(command, root, self.timeout)
        result.tool_name = self.name
        return result


class LintRunnerTool(SEAMTool):
    name = "lint_runner"
    description = "Run configured frontend linting."
    category = "frontend"
    input_schema = FrontendProjectInput
    allowed_agents = ["CodingAgent", "QAAgent"]
    risk_level = RiskLevel.MEDIUM
    timeout = 180

    def execute(self, tool_input: FrontendProjectInput, context: ToolExecutionContext) -> ToolResult:
        root = _safe_root(tool_input.project_root, context)
        if not _script_exists(root, "lint"):
            return _not_configured(self.name, "No lint script configured")
        result = _run(_build_script_command(root, "lint"), root, self.timeout)
        result.tool_name = self.name
        result.structured_data["errors"] = result.stderr
        result.structured_data["warnings"] = ""
        return result


class FrontendTestRunnerTool(SEAMTool):
    name = "frontend_test_runner"
    description = "Run configured frontend unit/component tests."
    category = "frontend"
    input_schema = FrontendProjectInput
    allowed_agents = ["QAAgent"]
    risk_level = RiskLevel.MEDIUM
    timeout = 180

    def execute(self, tool_input: FrontendProjectInput, context: ToolExecutionContext) -> ToolResult:
        root = _safe_root(tool_input.project_root, context)
        if not _script_exists(root, "test") and not _has_dependency(root, ["vitest", "jest", "@testing-library/react"]):
            return _not_configured(self.name, "No frontend test framework or test script configured")
        if _script_exists(root, "test"):
            command = _build_script_command(root, "test")
        else:
            vitest = _local_bin(root, "vitest")
            if not vitest:
                return _not_configured(self.name, "Vitest dependency found but local executable is unavailable")
            command = [vitest, "run"]
        result = _run(command, root, self.timeout)
        result.tool_name = self.name
        return result


class BuildRunnerTool(SEAMTool):
    name = "build_runner"
    description = "Build the frontend using the project's existing build configuration."
    category = "frontend"
    input_schema = FrontendProjectInput
    allowed_agents = ["CodingAgent", "QAAgent", "DeliveryAgent"]
    risk_level = RiskLevel.MEDIUM
    timeout = 240

    def execute(self, tool_input: FrontendProjectInput, context: ToolExecutionContext) -> ToolResult:
        root = _safe_root(tool_input.project_root, context)
        if not _script_exists(root, "build"):
            return _not_configured(self.name, "No build script configured")
        result = _run(_build_script_command(root, "build"), root, self.timeout)
        result.tool_name = self.name
        build_dir = "dist" if os.path.isdir(os.path.join(root, "dist")) else ".next" if os.path.isdir(os.path.join(root, ".next")) else None
        assets = []
        if build_dir:
            for current, _, files in os.walk(os.path.join(root, build_dir)):
                assets.extend(os.path.relpath(os.path.join(current, name), root).replace("\\", "/") for name in files[:50])
        result.structured_data.update({"build_directory": build_dir, "generated_assets": assets[:100]})
        return result


class PlaywrightRunnerTool(SEAMTool):
    name = "playwright_runner"
    description = "Run bounded Playwright browser validation if Playwright is already configured."
    category = "frontend"
    input_schema = PlaywrightInput
    allowed_agents = ["QAAgent"]
    risk_level = RiskLevel.MEDIUM
    timeout = 180

    def execute(self, tool_input: PlaywrightInput, context: ToolExecutionContext) -> ToolResult:
        root = _safe_root(tool_input.project_root, context)
        if not _has_dependency(root, ["@playwright/test", "playwright"]):
            return _not_configured(self.name, "Playwright is not configured")
        if not _script_exists(root, "test:e2e") and not os.path.exists(os.path.join(root, "playwright.config.ts")) and not os.path.exists(os.path.join(root, "playwright.config.js")):
            return _not_configured(self.name, "No Playwright config or e2e script configured")
        if _script_exists(root, "test:e2e"):
            command = _build_script_command(root, "test:e2e")
        else:
            playwright = _local_bin(root, "playwright")
            if not playwright:
                return _not_configured(self.name, "Playwright dependency found but local executable is unavailable")
            command = [playwright, "test"]
        result = _run(command, root, self.timeout)
        result.tool_name = self.name
        result.structured_data.update({"url": tool_input.url, "steps": [step.model_dump() for step in tool_input.steps], "console_errors": [], "network_errors": []})
        return result


class BrowserScreenshotTool(SEAMTool):
    name = "browser_screenshot"
    description = "Capture a browser screenshot through configured Playwright."
    category = "frontend"
    input_schema = BrowserScreenshotInput
    allowed_agents = ["QAAgent"]
    risk_level = RiskLevel.MEDIUM
    timeout = 120

    def execute(self, tool_input: BrowserScreenshotInput, context: ToolExecutionContext) -> ToolResult:
        root = _safe_root(tool_input.project_root, context)
        if not _has_dependency(root, ["@playwright/test", "playwright"]):
            return _not_configured(self.name, "Playwright is not configured")
        if not tool_input.url.startswith(("http://127.0.0.1", "http://localhost")):
            raise ValueError("browser_screenshot only allows localhost URLs")
        filename = Path(tool_input.filename).name
        screenshot_dir = os.path.join(root, "qa", "screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)
        screenshot_path = os.path.join(screenshot_dir, filename)
        script = (
            "const { chromium } = require('playwright');"
            "(async()=>{const b=await chromium.launch();const p=await b.newPage();"
            f"await p.goto('{tool_input.url}', {{waitUntil:'networkidle'}});"
            f"await p.screenshot({{path:'{screenshot_path.replace(os.sep, '/')}', fullPage:true}});"
            "await b.close();})().catch(e=>{console.error(e);process.exit(1);});"
        )
        result = _run(["node", "-e", script], root, self.timeout)
        result.tool_name = self.name
        rel = os.path.relpath(screenshot_path, root).replace("\\", "/")
        result.artifacts = [rel] if result.success else []
        result.structured_data.update({"screenshot": rel if result.success else None})
        return result


class AccessibilityCheckerTool(SEAMTool):
    name = "accessibility_checker"
    description = "Run configured frontend accessibility checks."
    category = "frontend"
    input_schema = FrontendProjectInput
    allowed_agents = ["QAAgent"]
    risk_level = RiskLevel.MEDIUM
    timeout = 180

    def execute(self, tool_input: FrontendProjectInput, context: ToolExecutionContext) -> ToolResult:
        root = _safe_root(tool_input.project_root, context)
        if _script_exists(root, "test:a11y"):
            result = _run(_build_script_command(root, "test:a11y"), root, self.timeout)
            result.tool_name = self.name
            return result
        if not _has_dependency(root, ["axe-core", "@axe-core/playwright", "jest-axe"]):
            return _not_configured(self.name, "No accessibility testing framework configured")
        return _not_configured(self.name, "Accessibility dependency found but no controlled a11y script configured")


def detect_frontend_capabilities(root: str) -> FrontendCapabilityProfile:
    package_json = _load_package_json(root)
    scripts = package_json.get("scripts") or {}
    deps = _dependencies(root)
    detected_files = [name for name in DETECTION_FILES if os.path.exists(os.path.join(root, name))]
    framework = "UNKNOWN"
    if "next" in deps or any(name.startswith("next.config.") for name in detected_files):
        framework = "next"
    elif "@angular/core" in deps or "angular.json" in detected_files:
        framework = "angular"
    elif "vue" in deps:
        framework = "vue"
    elif "react" in deps:
        framework = "react"

    build_system = "UNKNOWN"
    if "vite" in deps or any(name.startswith("vite.config.") for name in detected_files):
        build_system = "vite"
    elif framework == "next":
        build_system = "next"
    elif framework == "angular":
        build_system = "angular"

    language = "typescript" if "tsconfig.json" in detected_files or any(Path(root).rglob("*.tsx")) or any(Path(root).rglob("*.ts")) else "javascript" if package_json else "UNKNOWN"
    test_framework = "not_configured"
    if "vitest" in deps or any(name.startswith("vitest.config.") for name in detected_files):
        test_framework = "vitest"
    elif "jest" in deps or any(name.startswith("jest.config.") for name in detected_files):
        test_framework = "jest"
    elif "@testing-library/react" in deps:
        test_framework = "react_testing_library"

    package_manager = _detect_package_manager(root) if package_json else "UNKNOWN"
    dev_script = "dev" if "dev" in scripts else "start" if "start" in scripts else None
    build_output = ".next" if build_system == "next" else "dist" if build_system in {"vite", "angular"} else None
    typecheck_available = "typecheck" in scripts or bool("tsconfig.json" in detected_files and ("typescript" in deps or _local_bin(root, "tsc")))
    return FrontendCapabilityProfile(
        package_json=bool(package_json),
        framework=framework,
        language=language,
        package_manager=package_manager,
        build_system=build_system,
        available_scripts=sorted(scripts),
        typecheck_available=typecheck_available,
        lint_available="lint" in scripts or any(name.startswith("eslint.config") or name.startswith(".eslintrc") for name in detected_files),
        frontend_test_framework=test_framework,
        playwright_available="playwright" in deps or "@playwright/test" in deps or any(name.startswith("playwright.config.") for name in detected_files),
        accessibility_available="test:a11y" in scripts or any(name in deps for name in ["axe-core", "@axe-core/playwright", "jest-axe"]),
        dev_server_available=dev_script is not None,
        build_available="build" in scripts,
        dev_server_command=_script_command_if_present(root, dev_script) if dev_script else None,
        build_command=_script_command_if_present(root, "build"),
        test_command=_script_command_if_present(root, "test"),
        lint_command=_script_command_if_present(root, "lint"),
        typecheck_command=_script_command_if_present(root, "typecheck"),
        build_output_directory=build_output,
        detected_files=detected_files,
    )


def detect_frontend_project(root: str) -> Dict[str, Any]:
    profile = detect_frontend_capabilities(root)
    return {
        "package_detected": profile.package_json,
        "package_manager": None if profile.package_manager == "UNKNOWN" else profile.package_manager,
        "frameworks": [] if profile.framework == "UNKNOWN" else [profile.framework],
        "typescript": profile.language == "typescript",
        "scripts": profile.available_scripts,
        "has_src": os.path.isdir(os.path.join(root, "src")),
    }


def register_frontend_tools(registry=default_registry) -> None:
    for tool in [
        FrontendCapabilityDetectionTool(),
        NPMRunnerTool(),
        TypecheckRunnerTool(),
        LintRunnerTool(),
        FrontendTestRunnerTool(),
        PlaywrightRunnerTool(),
        BuildRunnerTool(),
        BrowserScreenshotTool(),
        AccessibilityCheckerTool(),
    ]:
        if not registry.is_registered(tool.name):
            registry.register(tool)
