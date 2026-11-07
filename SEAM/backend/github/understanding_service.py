import os
import re
import json
import logging
from typing import Dict, Any, List, Optional

from backend.github.intelligence_models import (
    DetailedRepositoryProfile,
    ProjectUnderstanding,
    utc_now,
)

logger = logging.getLogger(__name__)

# File size limit for inspection to prevent prompt bloat / memory issues
MAX_INSPECTION_FILE_SIZE = 100 * 1024  # 100 KB
MAX_FILES_TO_INSPECT = 300

FRAMEWORK_SIGNATURES = {
    "FastAPI": ["from fastapi import", "import fastapi"],
    "Flask": ["from flask import", "import flask"],
    "Django": ["django.db", "from django."],
    "React": ["from 'react'", "from \"react\"", "import React"],
    "Express": ["require('express')", "from 'express'"],
    "Next.js": ["next/router", "next/link", "next/navigation"],
    "Vue": ["from 'vue'", "vue-router"],
    "TailwindCSS": ["@tailwind", "tailwindcss"],
    "SQLAlchemy": ["from sqlalchemy", "import sqlalchemy"],
    "Prisma": ["@prisma/client", "datasource db"],
}

TEST_FRAMEWORKS = {
    "pytest": ["pytest", "def test_"],
    "unittest": ["unittest.TestCase"],
    "vitest": ["vitest", "describe(", "it("],
    "jest": ["jest", "describe(", "it("],
}

class ProjectUnderstandingService:
    def __init__(self, workspace_path: Optional[str] = None):
        self.workspace_path = workspace_path

    def analyze(
        self,
        workspace_path: str,
        owner: str = "",
        name: str = "",
        branch: str = "main",
        commit_sha: str = "HEAD"
    ) -> Tuple[DetailedRepositoryProfile, ProjectUnderstanding]:
        """Performs structured, evidence-based repository intelligence extraction and project understanding."""
        profile = DetailedRepositoryProfile(
            repository=f"{owner}/{name}" if owner and name else os.path.basename(workspace_path),
            owner=owner or "local",
            name=name or os.path.basename(workspace_path),
            branch=branch,
            commit_sha=commit_sha,
            freshness_status="CURRENT",
        )

        all_rel_paths = []
        for root, dirs, files in os.walk(workspace_path):
            if ".git" in dirs:
                dirs.remove(".git")
            if "node_modules" in dirs:
                dirs.remove("node_modules")
            if "__pycache__" in dirs:
                dirs.remove("__pycache__")
            if ".venv" in dirs:
                dirs.remove(".venv")
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), workspace_path).replace("\\", "/")
                all_rel_paths.append(rel)
                if len(all_rel_paths) >= MAX_FILES_TO_INSPECT:
                    break
            if len(all_rel_paths) >= MAX_FILES_TO_INSPECT:
                break

        profile.directory_structure = sorted(list({os.path.dirname(p) for p in all_rel_paths if os.path.dirname(p)}))[:20]

        # 1. Detect Languages and Package Managers
        languages = set()
        package_managers = set()
        frameworks = set()
        confirmed_findings = []
        inferred_findings = []
        unavailable_info = []

        for p in all_rel_paths:
            lower = p.lower()
            if lower.endswith(".py"):
                languages.add("Python")
            elif lower.endswith(".ts") or lower.endswith(".tsx"):
                languages.add("TypeScript")
            elif lower.endswith(".js") or lower.endswith(".jsx"):
                languages.add("JavaScript")
            elif lower.endswith(".go"):
                languages.add("Go")
            elif lower.endswith(".rs"):
                languages.add("Rust")
            elif lower.endswith(".java"):
                languages.add("Java")

            if lower.endswith("package.json"):
                package_managers.add("npm / yarn / pnpm")
                confirmed_findings.append(f"Node package manifest found at {p}")
            elif lower.endswith("requirements.txt") or lower.endswith("pyproject.toml"):
                package_managers.add("pip / poetry")
                confirmed_findings.append(f"Python package manifest found at {p}")
            elif lower.endswith("cargo.toml"):
                package_managers.add("cargo")
                confirmed_findings.append(f"Rust Cargo manifest found at {p}")
            elif lower.endswith("pom.xml"):
                package_managers.add("maven")
                confirmed_findings.append(f"Java Maven manifest found at {p}")

        profile.detected_languages = sorted(list(languages))
        profile.package_managers = sorted(list(package_managers))

        # 2. Inspect Entry Points, Frameworks, APIs, and Schemas
        entry_points = []
        api_routes = []
        database_schemas = []
        database_techs = set()
        test_commands = set()
        tests = []
        deployment_configs = []
        docker_ci_cd = []
        source_refs = []

        # Read README for project purpose
        readme_content = ""
        for r_name in ["README.md", "readme.md", "README"]:
            r_path = os.path.join(workspace_path, r_name)
            if os.path.exists(r_path):
                try:
                    with open(r_path, "r", encoding="utf-8", errors="ignore") as f:
                        readme_content = f.read(5000)
                    confirmed_findings.append(f"README documented at {r_name}")
                    source_refs.append({"file": r_name, "line": 1, "description": "Repository README"})
                    break
                except Exception:
                    pass

        # Inspect candidate code files within limit
        for rel_p in all_rel_paths:
            full_p = os.path.join(workspace_path, rel_p)
            base_n = os.path.basename(rel_p).lower()

            # Entry point candidates
            if base_n in ["main.py", "app.py", "server.py", "index.ts", "index.js", "main.ts", "main.js", "app.ts", "app.js"]:
                entry_points.append(rel_p)
                confirmed_findings.append(f"Application entry point: {rel_p}")
                source_refs.append({"file": rel_p, "line": 1, "description": "Entry point"})

            # Deployment & Docker & CI/CD
            if "dockerfile" in base_n:
                deployment_configs.append(rel_p)
                docker_ci_cd.append("Docker containerization")
                confirmed_findings.append(f"Dockerfile found at {rel_p}")
            elif "docker-compose" in base_n:
                deployment_configs.append(rel_p)
                docker_ci_cd.append("Docker Compose multi-service")
                confirmed_findings.append(f"Docker Compose found at {rel_p}")
            elif ".github/workflows" in rel_p.lower():
                docker_ci_cd.append(f"GitHub Actions CI/CD: {rel_p}")
                confirmed_findings.append(f"GitHub Action workflow at {rel_p}")

            # Inspect content for routes, schemas, tests if under size limit
            try:
                if os.path.getsize(full_p) > MAX_INSPECTION_FILE_SIZE:
                    continue
                with open(full_p, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Frameworks detection
                for fw_name, sigs in FRAMEWORK_SIGNATURES.items():
                    if any(sig in content for sig in sigs):
                        frameworks.add(fw_name)

                # API Routes detection (Python FastAPI/Flask or JS Express)
                if rel_p.endswith(".py"):
                    for idx, line in enumerate(content.splitlines(), start=1):
                        route_match = re.search(r"@(?:app|router|api)\.(get|post|put|delete|patch)\(\s*['\"]([^'\"]+)['\"]", line)
                        if route_match:
                            method, path = route_match.group(1).upper(), route_match.group(2)
                            api_routes.append({"method": method, "path": path, "file": rel_p, "line": idx, "confirmed": True})
                            source_refs.append({"file": rel_p, "line": idx, "description": f"API Endpoint: {method} {path}"})
                        # SQLAlchemy / ORM detection
                        if "class " in line and "(Base)" in line or "(db.Model)" in line:
                            cls_name = line.split("class ")[1].split("(")[0].strip()
                            database_schemas.append({"entity": cls_name, "file": rel_p, "line": idx, "type": "SQLAlchemy Model"})
                            database_techs.add("SQLAlchemy / Relational DB")
                            source_refs.append({"file": rel_p, "line": idx, "description": f"DB Model: {cls_name}"})

                if rel_p.endswith((".ts", ".js")):
                    for idx, line in enumerate(content.splitlines(), start=1):
                        route_match = re.search(r"(?:app|router)\.(get|post|put|delete|patch)\(\s*['\"]([^'\"]+)['\"]", line)
                        if route_match:
                            method, path = route_match.group(1).upper(), route_match.group(2)
                            api_routes.append({"method": method, "path": path, "file": rel_p, "line": idx, "confirmed": True})

                # Test file detection
                if "test" in base_n or "/tests/" in rel_p.replace("\\", "/"):
                    tests.append(rel_p)
                    if rel_p.endswith(".py"):
                        test_commands.add("python -m pytest")
                    elif rel_p.endswith((".ts", ".js", ".tsx", ".jsx")):
                        test_commands.add("npm test")

            except Exception:
                pass

        profile.application_entry_points = entry_points
        profile.frameworks = sorted(list(frameworks))
        profile.api_routes = api_routes[:30]
        profile.database_technologies = sorted(list(database_techs))
        profile.database_schemas = database_schemas[:20]
        profile.tests = tests[:20]
        profile.test_commands = sorted(list(test_commands))
        profile.deployment_configuration = deployment_configs
        profile.docker_ci_cd = docker_ci_cd
        profile.source_references = source_refs[:30]

        # Frontend / Backend architecture classification
        has_frontend = any(lang in ["TypeScript", "JavaScript"] for lang in languages) and any(fw in ["React", "Vue", "Next.js"] for fw in frameworks)
        has_backend = any(fw in ["FastAPI", "Flask", "Django", "Express"] for fw in frameworks) or "Python" in languages or "Go" in languages

        if has_frontend and has_backend:
            profile.frontend_architecture = "Single Page Application (React/JS/TS)"
            profile.backend_architecture = "Modular Web/API Backend"
        elif has_frontend:
            profile.frontend_architecture = "Frontend Client / Application"
            profile.backend_architecture = "None (Client-Only or External API)"
        elif has_backend:
            profile.frontend_architecture = "None (Headless Backend / API)"
            profile.backend_architecture = "Backend Service / API"
        else:
            profile.frontend_architecture = "Inferred / Undetermined"
            profile.backend_architecture = "Inferred / Undetermined"

        if not profile.database_technologies:
            unavailable_info.append("No explicit database connection or schema definitions found in repository.")
        if not profile.tests:
            unavailable_info.append("No automated test suites detected in inspected files.")
        if not profile.deployment_configuration:
            unavailable_info.append("No Docker or Kubernetes deployment manifests detected.")

        profile.confirmed_findings = confirmed_findings
        profile.inferred_findings = inferred_findings
        profile.unavailable_info = unavailable_info

        # 3. Build Structured Project Understanding (14 Sections)
        project_purpose = "General Software Application"
        if readme_content:
            first_lines = [l.strip() for l in readme_content.splitlines() if l.strip() and not l.startswith("#")][:3]
            if first_lines:
                project_purpose = " ".join(first_lines)

        understanding = ProjectUnderstanding(
            project_purpose=project_purpose,
            technology_stack=profile.detected_languages + profile.frameworks + profile.package_managers,
            architecture_and_entry_points=f"Entry points: {', '.join(entry_points) or 'None identified'}. Frontend: {profile.frontend_architecture or 'None'}. Backend: {profile.backend_architecture or 'None'}.",
            directory_structure=profile.directory_structure,
            main_modules=[{"path": p, "purpose": "Entry or core module"} for p in entry_points],
            api_surface=profile.api_routes,
            database_and_persistence={
                "technologies": profile.database_technologies or ["No persistent database detected"],
                "schemas": [s["entity"] for s in profile.database_schemas],
                "confirmed": bool(profile.database_technologies),
            },
            existing_tests={
                "test_files_count": len(profile.tests),
                "test_commands": profile.test_commands or ["None configured"],
                "test_files": profile.tests,
            },
            build_and_runtime_instructions={
                "package_managers": profile.package_managers,
                "commands": ["npm install && npm run build" if "npm / yarn / pnpm" in profile.package_managers else "pip install -r requirements.txt"],
            },
            deployment_configuration={
                "manifests": profile.deployment_configuration,
                "ci_cd": profile.docker_ci_cd,
            },
            architectural_limitations=[
                "Local workspace limited to checked-out snapshot",
                "Large files exceeding size threshold excluded from line analysis",
            ] + ([f"Missing automated tests"] if not profile.tests else []),
            potential_defects=[],
            improvement_opportunities=[
                "Add automated test coverage if test suites are sparse",
                "Ensure robust API request validation and structured schemas",
                "Add Docker containerization if deployment config is missing",
            ],
            uncertainties_requiring_input=[
                "Confirm intended enhancement scope before applying code changes",
            ],
            source_references=profile.source_references,
        )

        return profile, understanding

    def write_artifacts(
        self,
        project_dir: str,
        profile: DetailedRepositoryProfile,
        understanding: ProjectUnderstanding
    ) -> Dict[str, str]:
        """Writes project_understanding.json and project_understanding.md artifacts."""
        os.makedirs(project_dir, exist_ok=True)
        json_path = os.path.join(project_dir, "project_understanding.json")
        md_path = os.path.join(project_dir, "project_understanding.md")

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "profile": profile.model_dump(),
                "understanding": understanding.model_dump(),
            }, f, indent=2)

        md_content = f"""# Project Understanding & Repository Profile

**Repository**: `{profile.repository}`  
**Branch**: `{profile.branch}`  
**Commit**: `{profile.commit_sha}`  
**Analyzed At**: `{profile.analysis_timestamp}`  
**Freshness Status**: `{profile.freshness_status}`  

---

## 1. Project Purpose
{understanding.project_purpose}

## 2. Technology Stack
- **Languages**: {', '.join(profile.detected_languages) or 'None detected'}
- **Frameworks**: {', '.join(profile.frameworks) or 'None detected'}
- **Package Managers**: {', '.join(profile.package_managers) or 'None detected'}

## 3. Architecture & Entry Points
{understanding.architecture_and_entry_points}

## 4. Directory Structure
```text
{chr(10).join(f'- {d}' for d in profile.directory_structure) or '- (Flat root)'}
```

## 5. Main Modules
{chr(10).join(f"- `{m['path']}`: {m.get('purpose', '')}" for m in understanding.main_modules) or '- None identified'}

## 6. API Surface ({len(profile.api_routes)} endpoints detected)
| Method | Path | File | Line |
| :--- | :--- | :--- | :--- |
{chr(10).join(f"| {r['method']} | {r['path']} | `{r['file']}` | {r.get('line', '-')} |" for r in profile.api_routes) or '| - | No API routes detected | - | - |'}

## 7. Database & Persistence
- **Technologies**: {', '.join(profile.database_technologies) or 'None confirmed'}
- **Entities/Models**: {', '.join(s['entity'] for s in profile.database_schemas) or 'None detected'}

## 8. Existing Tests
- **Test files detected**: {len(profile.tests)}
- **Commands**: {', '.join(profile.test_commands) or 'None'}

## 9. Build and Runtime Instructions
- **Package Manager**: {', '.join(profile.package_managers) or 'Standard'}
- **Commands**: {', '.join(understanding.build_and_runtime_instructions.get('commands', []))}

## 10. Deployment Configuration
- **Manifests**: {', '.join(profile.deployment_configuration) or 'None'}
- **CI/CD**: {', '.join(profile.docker_ci_cd) or 'None'}

## 11. Architectural Limitations
{chr(10).join(f'- {item}' for item in understanding.architectural_limitations)}

## 12. Potential Defects
{chr(10).join(f'- {item}' for item in understanding.potential_defects) or '- None identified during baseline inspection'}

## 13. Improvement Opportunities
{chr(10).join(f'- {item}' for item in understanding.improvement_opportunities)}

## 14. Uncertainties Requiring User Input
{chr(10).join(f'- {item}' for item in understanding.uncertainties_requiring_input)}

---
*Generated by SEAM Repository Intelligence Engine.*
"""
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return {"json": json_path, "md": md_path}
