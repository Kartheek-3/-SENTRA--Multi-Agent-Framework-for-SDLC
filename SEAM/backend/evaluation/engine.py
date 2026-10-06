import json
import uuid
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from backend.events import event_bus
from backend.foundation.services import artifact_registry, event_store
from backend.models.evaluation import (
    AgentMetric,
    AutonomyMetrics,
    ContractMetrics,
    DefectMetrics,
    DeliveryMetrics,
    DomainRAGMetrics,
    E2EMetrics,
    EvaluationComparison,
    EvaluationRun,
    EvaluationSummary,
    PerformanceMetrics,
    QAMetrics,
    RepairMetrics,
    RequirementMetrics,
    ToolMetric,
)
from backend.models.state import ProjectState
from backend.tools.artifact_pipeline import write_text_artifact


AGENTS = ["AnalysisAgent", "PlanningAgent", "SupervisorAgent", "CodingAgent", "QAAgent", "DeliveryAgent"]
TOOL_CATEGORIES = {
    "rag": "Knowledge",
    "github": "Knowledge",
    "git": "Git",
    "file": "Filesystem",
    "frontend": "Frontend",
    "npm": "Frontend",
    "lint": "Frontend",
    "typecheck": "Frontend",
    "playwright": "Testing",
    "pytest": "Testing",
    "api_test": "Testing",
    "runtime": "Runtime",
    "docker": "Delivery",
    "build": "Delivery",
}


class EvaluationEngine:
    def evaluate(self, state: ProjectState, scenario_id: str = "UNSPECIFIED", baseline: Optional[Dict[str, Any]] = None, persist: bool = True) -> EvaluationSummary:
        event_bus.emit_sync("EVALUATION_STARTED", {
            "project_id": state.project_id,
            "agent": "EvaluationEngine",
            "summary": "Evaluation metrics computation started.",
        })
        try:
            events = [event.payload for event in event_store.list(project_id=state.project_id)]
            artifacts = artifact_registry.list(project_id=state.project_id)
            summary = self._build_summary(state, events, artifacts, scenario_id, baseline or {})
            state.evaluation_summary = summary
            self._emit_metric_events(state, summary)
            if persist:
                self.persist(state, summary)
            event_bus.emit_sync("EVALUATION_COMPLETED", {
                "project_id": state.project_id,
                "agent": "EvaluationEngine",
                "status": summary.run.status,
                "summary": "Evaluation metrics computation completed.",
            })
            return summary
        except Exception as exc:
            event_bus.emit_sync("EVALUATION_FAILED", {
                "project_id": state.project_id,
                "agent": "EvaluationEngine",
                "status": "FAILED",
                "error": str(exc),
                "summary": "Evaluation metrics computation failed.",
            })
            raise

    def persist(self, state: ProjectState, summary: EvaluationSummary) -> None:
        write_text_artifact(
            state,
            "evaluation/evaluation_results.json",
            summary.model_dump_json(indent=2),
            "SUMMARY",
            "EvaluationEngine",
        )
        write_text_artifact(
            state,
            "evaluation/SEAM_EVALUATION_REPORT.md",
            self._render_report(state, summary),
            "SUMMARY",
            "EvaluationEngine",
        )

    def _build_summary(self, state: ProjectState, events: List[Dict[str, Any]], artifacts: List[Any], scenario_id: str, baseline: Dict[str, Any]) -> EvaluationSummary:
        requirements = self._requirement_metrics(state)
        agents = self._agent_metrics(events)
        tools = self._tool_metrics(events)
        qa = self._qa_metrics(state)
        defects = self._defect_metrics(state)
        repairs = self._repair_metrics(state)
        e2e = self._e2e_metrics(state)
        contracts = self._contract_metrics(state)
        delivery = self._delivery_metrics(state)
        performance = self._performance_metrics(events)
        autonomy = self._autonomy_metrics(state, events)
        domain_rag = self._domain_rag_metrics(state, events)
        comparisons = self._baseline_comparison(baseline, {
            "requirement_coverage": requirements.requirement_coverage,
            "e2e_pass_rate": e2e.e2e_pass_rate,
            "contract_compliance_rate": contracts.contract_compliance_rate,
            "repair_resolution_rate": repairs.repair_resolution_rate,
            "tool_invocation_count": sum(tool.tool_invocation_count for tool in tools),
        })
        start_time, end_time, duration_ms = self._run_timing(events)
        run = EvaluationRun(
            evaluation_id=str(uuid.uuid4()),
            project_id=state.project_id,
            scenario_id=scenario_id,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            requirement_count=requirements.total_requirements,
            task_count=len(state.tasks),
            agent_count=len([agent for agent in agents if agent.invocation_count]),
            tool_invocation_count=sum(tool.tool_invocation_count for tool in tools),
            artifact_count=len(artifacts),
            defect_count=defects.total_defects,
            resolved_defect_count=repairs.successful_repairs,
            unresolved_defect_count=max(defects.total_defects - repairs.successful_repairs, 0),
            repair_iterations=len(state.repair_results),
            e2e_pass_rate=e2e.e2e_pass_rate,
            contract_pass_rate=contracts.contract_compliance_rate,
            qa_status=qa.final_qa_status,
            delivery_status=state.delivery_result.get("status", "NOT_AVAILABLE") if state.delivery_result else "NOT_AVAILABLE",
        )
        return EvaluationSummary(
            run=run,
            requirements=requirements,
            agents=agents,
            tools=tools,
            qa=qa,
            defects=defects,
            repairs=repairs,
            e2e=e2e,
            contracts=contracts,
            delivery=delivery,
            performance=performance,
            autonomy=autonomy,
            domain_rag=domain_rag,
            baseline_comparison=comparisons,
            limitations=[
                "Metrics are descriptive and depend on available ProjectState/EventStore/ArtifactRegistry evidence.",
                "No performance improvement or causality is claimed without a recorded baseline comparison.",
                "NOT_CONFIGURED and NOT_APPLICABLE are reported separately from failures.",
            ],
        )

    def _requirement_metrics(self, state: ProjectState) -> RequirementMetrics:
        reqs = state.structured_requirements.functional_requirements if state.structured_requirements else []
        total = len(reqs)
        req_ids = [getattr(req, "id", "") for req in reqs if getattr(req, "id", "")]
        planned = set()
        implemented = set()
        tested = set()
        delivered = set()
        traceability = []
        if state.project_plan:
            for task in state.project_plan.tasks:
                related = getattr(task, "related_requirements", []) or []
                planned.update(related)
                task_obj = state.tasks.get(task.task_id)
                if task_obj and task_obj.status == "completed":
                    implemented.update(related)
                    qa_res = task_obj.result.get("qa_result", {})
                    if qa_res and qa_res.get("passed"):
                        tested.update(related)
                traceability.append({"task_id": task.task_id, "requirements": related, "status": getattr(task_obj, "status", "unknown") if task_obj else "missing"})
        if state.delivery_result and state.delivery_result.get("status") in {"deployed", "packaged", "ready"}:
            delivered = set(tested)
        verified = len([rid for rid in req_ids if rid in implemented and rid in tested and rid in delivered])
        return RequirementMetrics(
            total_requirements=total,
            analyzed_requirements=total,
            planned_requirements=len([rid for rid in req_ids if rid in planned]),
            implemented_requirements=len([rid for rid in req_ids if rid in implemented]),
            tested_requirements=len([rid for rid in req_ids if rid in tested]),
            delivered_requirements=len([rid for rid in req_ids if rid in delivered]),
            requirement_coverage=self._rate(verified, total),
            traceability_evidence=traceability,
        )

    def _agent_metrics(self, events: List[Dict[str, Any]]) -> List[AgentMetric]:
        started_at: Dict[str, List[datetime]] = defaultdict(list)
        durations: Dict[str, List[int]] = defaultdict(list)
        counts = {agent: Counter() for agent in AGENTS}
        for event in events:
            agent = event.get("agent")
            if agent not in counts:
                continue
            event_type = event.get("event")
            if event_type == "AGENT_STARTED":
                counts[agent]["invocation"] += 1
                ts = self._parse_time(event.get("timestamp"))
                if ts:
                    started_at[agent].append(ts)
            elif event_type == "AGENT_COMPLETED":
                counts[agent]["success"] += 1
                self._record_duration(agent, event, started_at, durations)
            elif event_type == "AGENT_FAILED":
                counts[agent]["failure"] += 1
                self._record_duration(agent, event, started_at, durations)
            elif event_type == "AGENT_TIMEOUT":
                counts[agent]["timeout"] += 1
                self._record_duration(agent, event, started_at, durations)
        return [
            AgentMetric(
                agent=agent,
                invocation_count=counts[agent]["invocation"],
                success_count=counts[agent]["success"],
                failure_count=counts[agent]["failure"],
                timeout_count=counts[agent]["timeout"],
                average_duration_ms=self._average(durations[agent]),
                total_duration_ms=sum(durations[agent]),
                rework_count=counts[agent]["invocation"] - 1 if counts[agent]["invocation"] > 1 else 0,
            )
            for agent in AGENTS
        ]

    def _tool_metrics(self, events: List[Dict[str, Any]]) -> List[ToolMetric]:
        grouped: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"invoked": 0, "success": 0, "failed": 0, "blocked": 0, "denied": 0, "durations": []})
        for event in events:
            tool = event.get("tool_name") or event.get("tool")
            if not tool:
                continue
            category = self._tool_category(tool)
            event_type = event.get("event")
            if event_type == "TOOL_REQUESTED":
                grouped[category]["invoked"] += 1
            elif event_type == "TOOL_COMPLETED":
                grouped[category]["success"] += 1
                if event.get("duration_ms") is not None:
                    grouped[category]["durations"].append(int(event.get("duration_ms") or 0))
            elif event_type in {"TOOL_FAILED", "TOOL_TIMEOUT"}:
                grouped[category]["failed"] += 1
            elif event_type == "TOOL_PERMISSION_DENIED":
                grouped[category]["denied"] += 1
                grouped[category]["blocked"] += 1
            elif event_type == "TOOL_PERMISSION_CHECKED" and event.get("requires_approval"):
                grouped[category]["blocked"] += 1
        return [
            ToolMetric(
                category=category,
                tool_invocation_count=data["invoked"],
                success_rate=self._rate(data["success"], data["invoked"]),
                failure_rate=self._rate(data["failed"], data["invoked"]),
                blocked_count=data["blocked"],
                permission_denied_count=data["denied"],
                average_duration_ms=self._average(data["durations"]),
            )
            for category, data in sorted(grouped.items())
        ]

    def _qa_metrics(self, state: ProjectState) -> QAMetrics:
        qa_results = [task.result.get("qa_result") for task in state.tasks.values() if task.result.get("qa_result")]
        latest = qa_results[-1] if qa_results else {}
        issues = list(state.contract_issues)
        blocker_count = len([issue for issue in issues if issue.severity == "BLOCKER"])
        error_count = len([issue for issue in issues if issue.severity == "ERROR"])
        warning_count = len([issue for issue in issues if issue.severity == "WARNING"])
        runtime_failed = any(result.status == "FAIL" for result in state.runtime_contract_results)
        e2e_failed = any(result.status == "FAIL" for result in state.e2e_results)
        return QAMetrics(
            static_validation_result="PASS" if latest.get("passed") else ("FAIL" if latest else "NOT_AVAILABLE"),
            contract_result="FAIL" if error_count or blocker_count else ("PASS" if state.full_stack_contract else "NOT_CONFIGURED"),
            runtime_contract_result="FAIL" if runtime_failed else ("PASS" if state.runtime_contract_results else "NOT_CONFIGURED"),
            frontend_validation_result=state.frontend_execution.get("validation_status", "NOT_CONFIGURED"),
            backend_validation_result="PASS" if latest.get("passed") else ("FAIL" if latest else "NOT_AVAILABLE"),
            e2e_result="FAIL" if e2e_failed else ("PASS" if state.e2e_results else "NOT_CONFIGURED"),
            security_result=state.release_readiness.security_status if state.release_readiness else "NOT_AVAILABLE",
            final_qa_status="PASS" if latest.get("passed") else ("FAIL" if latest else state.latest_qa_status.upper()),
            qa_defect_count=len(state.defect_locations) + len(issues),
            blocker_count=blocker_count,
            error_count=error_count,
            warning_count=warning_count,
        )

    def _defect_metrics(self, state: ProjectState) -> DefectMetrics:
        layers = Counter(defect.layer for defect in state.defect_locations)
        return DefectMetrics(
            total_defects=len(state.defect_locations),
            frontend_defects=layers["FRONTEND"],
            backend_defects=layers["BACKEND"],
            api_contract_defects=layers["API_CONTRACT"],
            database_defects=layers["DATABASE"],
            runtime_defects=layers["RUNTIME"],
            authentication_defects=layers["AUTHENTICATION"],
            unknown_defects=layers["UNKNOWN"],
        )

    def _repair_metrics(self, state: ProjectState) -> RepairMetrics:
        results = Counter(result.status for result in state.repair_results)
        plans = Counter(plan.status for plan in state.repair_plans)
        targeted_pass = len([item for item in state.targeted_verifications if item.status == "PASS"])
        regression_pass = len([item for item in state.regression_results if item.status == "PASS"])
        resolved = len([plan for plan in state.repair_plans if plan.status == "RESOLVED"])
        return RepairMetrics(
            repair_plans=len(state.repair_plans),
            successful_repairs=results["SUCCESS"] + resolved,
            failed_repairs=results["FAILED"],
            blocked_repairs=results["BLOCKED"] + plans["BLOCKED"],
            needs_review_repairs=plans["NEEDS_REVIEW"],
            average_repair_iterations=self._average([len(state.repair_results)]) if state.repair_plans else "NOT_APPLICABLE",
            maximum_repair_iterations=state.max_repair_iterations,
            targeted_verification_pass_rate=self._rate(targeted_pass, len(state.targeted_verifications)),
            regression_pass_rate=self._rate(regression_pass, len(state.regression_results)),
            repair_resolution_rate=self._rate(resolved, len(state.repair_plans)),
        )

    def _e2e_metrics(self, state: ProjectState) -> E2EMetrics:
        counts = Counter(result.status for result in state.e2e_results)
        step_failures = sum(1 for result in state.e2e_results for step in result.steps if step.status == "FAIL")
        executed = counts["PASS"] + counts["FAIL"] + counts["BLOCKED"]
        return E2EMetrics(
            scenarios_generated=len(state.e2e_scenarios),
            scenarios_executed=executed,
            scenarios_passed=counts["PASS"],
            scenarios_failed=counts["FAIL"],
            scenarios_blocked=counts["BLOCKED"],
            scenarios_not_configured=counts["NOT_CONFIGURED"] + max(len(state.e2e_scenarios) - len(state.e2e_results), 0),
            execution_duration_ms=sum(result.duration_ms for result in state.e2e_results),
            step_failure_count=step_failures,
            e2e_pass_rate=self._rate(counts["PASS"], executed),
        )

    def _contract_metrics(self, state: ProjectState) -> ContractMetrics:
        total_contracts = len(state.full_stack_contract.api_contracts) if state.full_stack_contract else 0
        issues = state.contract_issues or (state.full_stack_contract.issues if state.full_stack_contract else [])
        runtime_issues = sum(len(result.issues) for result in state.runtime_contract_results)
        unresolved = len([issue for issue in issues if issue.severity in {"ERROR", "BLOCKER"}]) + len([result for result in state.runtime_contract_results if result.status == "FAIL"])
        categories = Counter(issue.category for issue in issues)
        compliant = max(total_contracts - unresolved, 0)
        return ContractMetrics(
            total_contracts=total_contracts,
            static_contract_issues=len(issues),
            runtime_contract_issues=runtime_issues,
            endpoint_mismatches=categories["ENDPOINT_MISMATCH"],
            method_mismatches=categories["METHOD_MISMATCH"],
            request_mismatches=categories["REQUEST_MISMATCH"],
            response_mismatches=categories["RESPONSE_MISMATCH"],
            database_mapping_issues=categories["DATABASE_MAPPING"],
            contract_compliance_rate=self._rate(compliant, total_contracts),
        )

    def _delivery_metrics(self, state: ProjectState) -> DeliveryMetrics:
        readiness = state.release_readiness
        delivery = state.delivery_result or {}
        return DeliveryMetrics(
            release_ready=readiness.status == "READY" if readiness else False,
            release_blocked=readiness.status in {"BLOCKED", "NOT_READY"} if readiness else False,
            deployment_target=state.deployment_profile.target if state.deployment_profile else "NOT_CONFIGURED",
            artifact_generation="PASS" if state.deployment_artifacts else "NOT_AVAILABLE",
            secret_scan_result=readiness.security_status if readiness else "NOT_AVAILABLE",
            packaging_result="PASS" if delivery.get("package_created") else ("FAIL" if delivery.get("errors") else "NOT_AVAILABLE"),
            post_deployment_verification=state.post_deployment_verification.status if state.post_deployment_verification else "NOT_CONFIGURED",
            rollback_availability=state.rollback_info.rollback_status if state.rollback_info else "NOT_CONFIGURED",
        )

    def _performance_metrics(self, events: List[Dict[str, Any]]) -> PerformanceMetrics:
        _, _, total = self._run_timing(events)
        tool_time = sum(int(event.get("duration_ms") or 0) for event in events if event.get("event") == "TOOL_COMPLETED")
        breakdown = self._stage_durations(events)
        return PerformanceMetrics(
            total_workflow_duration_ms=total,
            agent_processing_time_ms=sum(breakdown.values()),
            tool_execution_time_ms=tool_time,
            qa_time_ms=breakdown.get("QA", 0),
            repair_time_ms=breakdown.get("Repair", 0),
            delivery_time_ms=breakdown.get("Delivery", 0),
            breakdown_by_stage=breakdown,
        )

    def _autonomy_metrics(self, state: ProjectState, events: List[Dict[str, Any]]) -> AutonomyMetrics:
        approval_requests = len([event for event in events if event.get("requires_approval")])
        blocked = len([event for event in events if event.get("event") in {"TOOL_PERMISSION_DENIED", "DELIVERY_BLOCKED", "RELEASE_BLOCKED"}])
        return AutonomyMetrics(
            approval_requests=approval_requests,
            blocked_actions=blocked,
            autonomous_repair_iterations=len(state.repair_results),
            autonomous_successful_repairs=len([result for result in state.repair_results if result.status == "SUCCESS"]),
        )

    def _domain_rag_metrics(self, state: ProjectState, events: List[Dict[str, Any]]) -> DomainRAGMetrics:
        source_types = sorted({item.source_type for item in state.domain_context.items}) if state.domain_context else []
        rag_events = [event for event in events if "rag" in str(event.get("tool_name", "")).lower() or "knowledge" in str(event.get("summary", "")).lower()]
        retrieved_docs = len(state.retrieved_context)
        if state.domain_context:
            retrieved_docs += len(state.domain_context.items)
        return DomainRAGMetrics(
            domain_detected=state.domain_identification.domain if state.domain_identification else (state.domain or "NOT_AVAILABLE"),
            knowledge_retrieved=bool(state.retrieved_context or (state.domain_context and state.domain_context.items)),
            knowledge_sources_used=len(source_types),
            source_types=source_types,
            domain_specific_constraints_included=len(state.structured_requirements.constraints) if state.structured_requirements else 0,
            domain_related_qa_issues=len([item for item in state.qa_feedback if state.domain and state.domain.lower() in item.lower()]),
            retrieval_count=len(rag_events),
            retrieval_success=len([event for event in rag_events if event.get("event") == "TOOL_COMPLETED"]),
            documents_retrieved=retrieved_docs,
            domain_retrieval_count=len(state.domain_context.items) if state.domain_context else 0,
            repository_knowledge_retrieval_count=len(state.github_context or {}),
        )

    def _baseline_comparison(self, baseline: Dict[str, Any], seam: Dict[str, Any]) -> List[EvaluationComparison]:
        comparisons = []
        for metric, baseline_value in baseline.items():
            if metric not in seam:
                continue
            seam_value = seam[metric]
            absolute = None
            relative = None
            if isinstance(baseline_value, (int, float)) and isinstance(seam_value, (int, float)):
                absolute = float(seam_value) - float(baseline_value)
                relative = None if baseline_value == 0 else absolute / float(baseline_value)
            comparisons.append(EvaluationComparison(metric=metric, baseline_value=baseline_value, seam_value=seam_value, absolute_difference=absolute, relative_difference=relative))
        return comparisons

    def _emit_metric_events(self, state: ProjectState, summary: EvaluationSummary) -> None:
        for metric, value in {
            "requirement_coverage": summary.requirements.requirement_coverage,
            "e2e_pass_rate": summary.e2e.e2e_pass_rate,
            "contract_compliance_rate": summary.contracts.contract_compliance_rate,
            "repair_resolution_rate": summary.repairs.repair_resolution_rate,
            "tool_invocation_count": summary.run.tool_invocation_count,
        }.items():
            event_bus.emit_sync("EVALUATION_METRIC_COMPUTED", {
                "project_id": state.project_id,
                "agent": "EvaluationEngine",
                "metric": metric,
                "value": value,
                "summary": f"{metric}: {value}",
            })

    def _render_report(self, state: ProjectState, summary: EvaluationSummary) -> str:
        baseline = "Available" if summary.baseline_comparison else "No recorded baseline comparison was provided."
        return f"""# SEAM Evaluation Report

## Executive Summary

Project: {state.project_id}
Scenario: {summary.run.scenario_id}
Status: {summary.run.status}
Duration: {summary.run.duration_ms} ms

This report contains descriptive measurements only. It does not claim superiority or causality without recorded baseline evidence.

## Scenario Description

{state.user_requirement or 'NOT_AVAILABLE'}

## Architecture Used

Agents: Analysis, Planning, Supervisor, Coding, QA, Delivery.
Architecture: {state.project_plan.system_design.architecture_style if state.project_plan and state.project_plan.system_design else 'NOT_AVAILABLE'}

## Workflow Execution

- Requirements: {summary.run.requirement_count}
- Tasks: {summary.run.task_count}
- Agents invoked: {summary.run.agent_count}
- Tool invocations: {summary.run.tool_invocation_count}
- Artifacts: {summary.run.artifact_count}

## Requirement Coverage

- Coverage: {summary.requirements.requirement_coverage}
- Analyzed: {summary.requirements.analyzed_requirements}
- Planned: {summary.requirements.planned_requirements}
- Implemented: {summary.requirements.implemented_requirements}
- Tested: {summary.requirements.tested_requirements}
- Delivered: {summary.requirements.delivered_requirements}

## Tool Metrics

{self._table(['Category', 'Invocations', 'Success Rate', 'Failure Rate', 'Blocked'], [[tool.category, tool.tool_invocation_count, tool.success_rate, tool.failure_rate, tool.blocked_count] for tool in summary.tools])}

## Agent Metrics

{self._table(['Agent', 'Invocations', 'Success', 'Failure', 'Timeout', 'Avg ms'], [[agent.agent, agent.invocation_count, agent.success_count, agent.failure_count, agent.timeout_count, agent.average_duration_ms] for agent in summary.agents])}

## Contract Metrics

- Total contracts: {summary.contracts.total_contracts}
- Static issues: {summary.contracts.static_contract_issues}
- Runtime issues: {summary.contracts.runtime_contract_issues}
- Compliance: {summary.contracts.contract_compliance_rate}

## QA Metrics

- Final QA: {summary.qa.final_qa_status}
- Static: {summary.qa.static_validation_result}
- Runtime contract: {summary.qa.runtime_contract_result}
- Security: {summary.qa.security_result}
- Defects: {summary.qa.qa_defect_count}

## E2E Metrics

- Generated: {summary.e2e.scenarios_generated}
- Executed: {summary.e2e.scenarios_executed}
- Passed: {summary.e2e.scenarios_passed}
- Failed: {summary.e2e.scenarios_failed}
- Pass rate: {summary.e2e.e2e_pass_rate}

## Defect Metrics

- Total: {summary.defects.total_defects}
- Frontend: {summary.defects.frontend_defects}
- Backend: {summary.defects.backend_defects}
- API contract: {summary.defects.api_contract_defects}
- Runtime: {summary.defects.runtime_defects}
- Unknown: {summary.defects.unknown_defects}

## Repair Metrics

- Plans: {summary.repairs.repair_plans}
- Successful: {summary.repairs.successful_repairs}
- Failed: {summary.repairs.failed_repairs}
- Resolution rate: {summary.repairs.repair_resolution_rate}

## Delivery Metrics

- Release ready: {summary.delivery.release_ready}
- Release blocked: {summary.delivery.release_blocked}
- Deployment target: {summary.delivery.deployment_target}
- Packaging: {summary.delivery.packaging_result}
- Rollback: {summary.delivery.rollback_availability}

## Runtime Metrics

- Runtime status: {state.runtime_status}
- Runtime URL: {state.runtime_base_url or 'NOT_CONFIGURED'}

## RAG/Domain Metrics

- Domain detected: {summary.domain_rag.domain_detected}
- Knowledge retrieved: {summary.domain_rag.knowledge_retrieved}
- Source types: {', '.join(summary.domain_rag.source_types) if summary.domain_rag.source_types else 'NOT_AVAILABLE'}
- Retrieval count: {summary.domain_rag.retrieval_count}
- Documents retrieved: {summary.domain_rag.documents_retrieved}

## Baseline Comparison

{baseline}

## Limitations

{chr(10).join(f'- {item}' for item in summary.limitations)}
"""

    def _table(self, headers: List[str], rows: List[List[Any]]) -> str:
        if not rows:
            return "No recorded data."
        header = "| " + " | ".join(headers) + " |"
        sep = "| " + " | ".join(["---"] * len(headers)) + " |"
        body = ["| " + " | ".join(str(item) for item in row) + " |" for row in rows]
        return "\n".join([header, sep, *body])

    def _stage_durations(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        mapping = {
            "AnalysisAgent": "Analysis",
            "PlanningAgent": "Planning",
            "CodingAgent": "Coding",
            "QAAgent": "QA",
            "DeliveryAgent": "Delivery",
        }
        starts: Dict[str, List[datetime]] = defaultdict(list)
        totals: Dict[str, int] = defaultdict(int)
        for event in events:
            agent = event.get("agent")
            stage = mapping.get(agent)
            if not stage:
                continue
            ts = self._parse_time(event.get("timestamp"))
            if not ts:
                continue
            if event.get("event") == "AGENT_STARTED":
                starts[stage].append(ts)
            elif event.get("event") in {"AGENT_COMPLETED", "AGENT_FAILED", "AGENT_TIMEOUT"} and starts[stage]:
                totals[stage] += max(int((ts - starts[stage].pop(0)).total_seconds() * 1000), 0)
        totals["Repair"] = sum(totals.get(stage, 0) for stage in ["Coding", "QA"] if stage in totals)
        return dict(totals)

    def _run_timing(self, events: List[Dict[str, Any]]) -> tuple[Optional[str], Optional[str], int]:
        times = [self._parse_time(event.get("timestamp")) for event in events]
        times = [time for time in times if time]
        if not times:
            return None, None, 0
        start = min(times)
        end = max(times)
        return start.isoformat(), end.isoformat(), int((end - start).total_seconds() * 1000)

    def _record_duration(self, agent: str, event: Dict[str, Any], started_at: Dict[str, List[datetime]], durations: Dict[str, List[int]]) -> None:
        if not started_at[agent]:
            return
        end = self._parse_time(event.get("timestamp"))
        start = started_at[agent].pop(0)
        if end:
            durations[agent].append(max(int((end - start).total_seconds() * 1000), 0))

    def _tool_category(self, tool_name: str) -> str:
        lowered = tool_name.lower()
        for key, category in TOOL_CATEGORIES.items():
            if key in lowered:
                return category
        return "Backend"

    def _rate(self, numerator: int, denominator: int) -> Any:
        if denominator == 0:
            return "NOT_APPLICABLE"
        return round(numerator / denominator, 4)

    def _average(self, values: Iterable[int]) -> Any:
        values = list(values)
        if not values:
            return "NOT_APPLICABLE"
        return round(sum(values) / len(values), 2)

    def _parse_time(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
