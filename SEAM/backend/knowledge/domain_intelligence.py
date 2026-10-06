import json
from datetime import datetime, timezone
from typing import Iterable, List, Optional

from backend.events import event_bus
from backend.models.domain import (
    DomainContext,
    DomainIdentification,
    DomainTraceability,
    RetrievedKnowledge,
)


DOMAIN_PROFILES = {
    "healthcare": {
        "phrases": [
            "hospital", "patient", "doctor", "appointment", "clinic", "medical",
            "healthcare", "physician", "prescription", "diagnosis",
        ],
        "subdomains": {
            "hospital appointment management": ["appointment", "doctor availability", "booking", "patient registration"],
            "clinical records": ["medical record", "diagnosis", "prescription"],
        },
        "requirements": ["patient and doctor role workflows", "appointment lifecycle management"],
        "constraints": ["protect sensitive healthcare data", "record audit trails for sensitive actions"],
        "concerns": ["authentication", "authorization", "audit logging", "data minimization"],
    },
    "ecommerce": {
        "phrases": [
            "e-commerce", "ecommerce", "shopping", "cart", "checkout", "product",
            "catalog", "order", "inventory", "payment",
        ],
        "subdomains": {
            "shopping and order management": ["cart", "checkout", "order", "product catalog"],
            "inventory and payment": ["inventory", "payment", "stock"],
        },
        "requirements": ["catalog browsing", "cart and order workflow", "inventory consistency"],
        "constraints": ["payment data must be isolated", "orders need transaction boundaries"],
        "concerns": ["checkout integrity", "payment safety", "inventory race conditions"],
    },
    "finance": {
        "phrases": [
            "finance", "financial", "expense", "transaction", "ledger", "account",
            "budget", "reporting", "invoice", "balance",
        ],
        "subdomains": {
            "expense and transaction tracking": ["expense", "transaction", "budget", "reporting"],
            "ledger management": ["ledger", "account", "balance"],
        },
        "requirements": ["transaction recording", "financial reporting", "auditability"],
        "constraints": ["transaction integrity is required", "sensitive financial data must be protected"],
        "concerns": ["authorization", "audit logging", "consistency", "reconciliation"],
    },
    "general": {
        "phrases": ["software", "application", "dashboard", "api", "web app", "system"],
        "subdomains": {},
        "requirements": ["clear functional boundaries"],
        "constraints": ["validated inputs and predictable persistence"],
        "concerns": ["security", "testing", "maintainability"],
    },
}


DOMAIN_ALIASES = {
    "e-commerce": "ecommerce",
    "commerce": "ecommerce",
    "shopping": "ecommerce",
    "medical": "healthcare",
    "hospital": "healthcare",
    "financial": "finance",
}


def normalize_domain(domain: str) -> str:
    value = (domain or "").strip().lower().replace("_", "-")
    return DOMAIN_ALIASES.get(value, value if value in DOMAIN_PROFILES else "general")


def _token_text(parts: Iterable[str]) -> str:
    return " ".join(part for part in parts if part).lower()


class DomainIntelligenceService:
    def identify(self, requirement: str, analysis=None) -> DomainIdentification:
        analysis_domain = getattr(analysis, "application_domain", "") if analysis else ""
        actors = getattr(analysis, "actors", []) if analysis else []
        entities = getattr(analysis, "entities", []) if analysis else []
        constraints = getattr(analysis, "constraints", []) if analysis else []
        technical = getattr(analysis, "technical_considerations", []) if analysis else []
        text = _token_text([requirement, analysis_domain, *actors, *entities, *constraints, *technical])

        scores = {}
        evidence = {}
        for domain, profile in DOMAIN_PROFILES.items():
            hits = [phrase for phrase in profile["phrases"] if phrase in text]
            scores[domain] = len(hits)
            evidence[domain] = hits

        normalized_analysis_domain = normalize_domain(analysis_domain)
        if normalized_analysis_domain in scores and normalized_analysis_domain != "general":
            scores[normalized_analysis_domain] += 2
            evidence[normalized_analysis_domain].append(f"analysis_domain:{analysis_domain}")

        domain = max(scores, key=scores.get)
        if scores[domain] == 0:
            domain = "general"

        profile = DOMAIN_PROFILES[domain]
        subdomain = None
        for candidate, phrases in profile["subdomains"].items():
            if any(phrase in text for phrase in phrases):
                subdomain = candidate
                break

        retrieval_terms = list(dict.fromkeys([
            domain,
            subdomain or "",
            *evidence.get(domain, []),
            *profile["requirements"],
            *profile["concerns"],
        ]))
        retrieval_terms = [term for term in retrieval_terms if term]
        confidence = min(1.0, 0.35 + (scores[domain] * 0.12)) if domain != "general" else 0.45

        return DomainIdentification(
            domain=domain,
            subdomain=subdomain,
            relevant_technologies=list(dict.fromkeys(getattr(analysis, "technical_considerations", []) if analysis else [])),
            domain_requirements=profile["requirements"],
            domain_constraints=profile["constraints"],
            domain_sensitive_concerns=profile["concerns"],
            retrieval_terms=retrieval_terms,
            confidence=confidence,
            evidence=evidence.get(domain, []),
        )

    def build_query(self, requirement: str, identification: DomainIdentification, current_task: Optional[str] = None) -> str:
        parts = [
            requirement,
            identification.domain,
            identification.subdomain or "",
            current_task or "",
            *identification.domain_requirements,
            *identification.domain_constraints,
            *identification.domain_sensitive_concerns,
            *identification.retrieval_terms,
        ]
        return " ".join(part for part in parts if part)

    def retrieve_context(
        self,
        state,
        current_task: Optional[str] = None,
        top_k: int = 6,
        service=None,
    ) -> DomainContext:
        from backend.knowledge.knowledge_service import KnowledgeService

        identification = state.domain_identification or self.identify(state.user_requirement, state.structured_requirements)
        state.domain_identification = identification
        state.domain = identification.domain
        if state.structured_requirements:
            state.structured_requirements.domain_identification = identification

        query = self.build_query(state.user_requirement, identification, current_task)
        ks = service or KnowledgeService()
        event_bus.emit_sync("DOMAIN_CONTEXT_RETRIEVAL_STARTED", {
            "project_id": state.project_id,
            "agent": "RAG",
            "summary": f"Retrieving validated {identification.domain} domain knowledge.",
            "domain": identification.domain,
        })
        result = ks.retrieve_domain_aware(
            query=query,
            domain=identification.domain,
            top_k=top_k,
            relevance_threshold=0.25,
        )

        context = DomainContext(
            detected_domain=identification,
            retrieval_query=query,
            retrieved_documents=[RetrievedKnowledge(**item) for item in result["results"]],
            status="VALIDATED_DOMAIN_KNOWLEDGE_FOUND" if result["results"] else "NO_VALIDATED_DOMAIN_KNOWLEDGE_FOUND",
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
        state.domain_context = context
        state.domain_traceability = self.build_traceability(state, context)
        event_bus.emit_sync("DOMAIN_CONTEXT_RETRIEVED", {
            "project_id": state.project_id,
            "agent": "RAG",
            "summary": f"Retrieved {len(context.retrieved_documents)} validated domain knowledge items.",
            "domain": identification.domain,
            "result_count": len(context.retrieved_documents),
            "sources": [item.source for item in context.retrieved_documents],
        })
        return context

    def build_traceability(self, state, context: DomainContext) -> DomainTraceability:
        sources = [item.source for item in context.retrieved_documents]
        topics = [item.topic or item.category for item in context.retrieved_documents]
        planning = [f"Consider {topic} from {source}" for topic, source in zip(topics, sources)]
        coding = [f"Use domain constraints when implementing {topic}" for topic in topics[:4]]
        qa = [f"Validate {topic} against retrieved {context.detected_domain.domain} knowledge" for topic in topics[:4]]
        return DomainTraceability(
            user_requirement=state.user_requirement,
            detected_domain=context.detected_domain.domain,
            subdomain=context.detected_domain.subdomain,
            retrieval_query=context.retrieval_query,
            retrieved_sources=sources,
            planning_impact=planning,
            coding_impact=coding,
            qa_impact=qa,
            metadata={"status": context.status, "knowledge_count": len(context.retrieved_documents)},
        )

    def format_for_prompt(self, context: Optional[DomainContext]) -> str:
        if not context:
            return "NO_VALIDATED_DOMAIN_KNOWLEDGE_FOUND"
        lines = [
            "--- DOMAIN-AWARE CONTEXT ---",
            f"Detected domain: {context.detected_domain.domain}",
            f"Subdomain: {context.detected_domain.subdomain or 'not identified'}",
            f"Status: {context.status}",
            f"Retrieval query: {context.retrieval_query}",
        ]
        for item in context.retrieved_documents:
            lines.append(
                f"Source: {item.source} | Domain: {item.domain} | Category: {item.category} | "
                f"Topic: {item.topic} | Organization: {item.organization} | Source Type: {item.source_type} | "
                f"URL: {item.url or 'LOCAL'} | Status: {item.status} | Score: {item.relevance_score:.3f}\n{item.content}"
            )
        return "\n\n".join(lines)

    def persist_artifacts(self, state) -> List[dict]:
        if not state.domain_context:
            return []
        from backend.tools.artifact_pipeline import write_text_artifact

        context = state.domain_context
        traceability = state.domain_traceability or self.build_traceability(state, context)
        md_sources = "\n".join(
            f"- {item.source} | domain={item.domain} | category={item.category} | "
            f"topic={item.topic} | organization={item.organization} | source_type={item.source_type} | "
            f"url={item.url or 'LOCAL'} | status={item.status} | score={item.relevance_score:.3f} | "
            f"version={item.document_version or item.version}"
            for item in context.retrieved_documents
        ) or "- NO_VALIDATED_DOMAIN_KNOWLEDGE_FOUND"
        context_md = f"""# Domain Context

## Detected Domain
{context.detected_domain.domain}

## Subdomain
{context.detected_domain.subdomain or 'NOT_IDENTIFIED'}

## Retrieval Query
{context.retrieval_query}

## Status
{context.status}

## Retrieved Knowledge
{md_sources}
"""
        trace_md = f"""# Domain Traceability

## User Requirement
{traceability.user_requirement}

## Detected Domain
{traceability.detected_domain}

## Retrieved Knowledge
{chr(10).join(f'- {item}' for item in traceability.retrieved_sources) if traceability.retrieved_sources else '- NO_VALIDATED_DOMAIN_KNOWLEDGE_FOUND'}

## Planning Impact
{chr(10).join(f'- {item}' for item in traceability.planning_impact) if traceability.planning_impact else '- No domain-specific planning impact recorded.'}

## Coding Impact
{chr(10).join(f'- {item}' for item in traceability.coding_impact) if traceability.coding_impact else '- No domain-specific coding impact recorded.'}

## QA Impact
{chr(10).join(f'- {item}' for item in traceability.qa_impact) if traceability.qa_impact else '- No domain-specific QA impact recorded.'}
"""
        artifacts = [
            write_text_artifact(state, "analysis/domain_context.md", context_md, "KNOWLEDGE", "AnalysisAgent", knowledge_kind="domain_context"),
            write_text_artifact(state, "analysis/domain_context.json", context.model_dump_json(indent=2), "KNOWLEDGE", "AnalysisAgent", knowledge_kind="domain_context"),
            write_text_artifact(state, "analysis/domain_traceability.md", trace_md, "KNOWLEDGE", "AnalysisAgent", knowledge_kind="domain_traceability"),
            write_text_artifact(state, "analysis/domain_traceability.json", traceability.model_dump_json(indent=2), "KNOWLEDGE", "AnalysisAgent", knowledge_kind="domain_traceability"),
        ]
        event_bus.emit_sync("DOMAIN_ARTIFACTS_PERSISTED", {
            "project_id": state.project_id,
            "agent": "AnalysisAgent",
            "summary": "Domain context and traceability artifacts persisted.",
            "paths": [artifact["path"] for artifact in artifacts],
        })
        return artifacts

    def persist_traceability(self, state, agent: str, impact: str) -> None:
        if not state.domain_traceability:
            return
        state.domain_traceability.metadata[f"{agent}_impact"] = impact
        try:
            self.persist_artifacts(state)
        except Exception as exc:
            state.errors.append(f"Domain traceability update failed for {agent}: {exc}")
