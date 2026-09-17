# SEAM Scale-Aware Engineering Methodology

## Overview
SEAM now features dynamic Scale-Aware Engineering. It evaluates user requirements to determine project scale (`SMALL`, `MEDIUM`, `LARGE`, `ENTERPRISE`) and adapts the entire autonomous engineering pipeline—from architectural design to parallel task execution, QA stringency, and deployment topology.

## Scale Assessment
The **Analysis Agent** extracts explicitly defined requirements and infers up to 20 engineering dimensions (functional complexity, transaction volume, geographic distribution, etc.). Missing information is explicitly marked as `UNKNOWN` or `ASSUMPTION` rather than hallucinated.

## Progressive Complexity & Anti-Overengineering
The **Planning Agent** enforces the principle: *START SIMPLE → ADD COMPLEXITY ONLY WHEN REQUIRED*.
A 100-user application will never receive Kubernetes or Kafka. A 1-million-user global platform will never be designed as a single-process monolith.

## Architecture Decisions & Evolution
Every infrastructure component introduced into the `SystemDesign` must be accompanied by an explicit `ArchitectureDecision` record justifying its purpose and complexity. Medium to Enterprise projects also generate a `ScaleEvolutionPlan` to chart the path from MVP to production-scale.

## Scale-Aware Agent Adaptation
- **Coding Agent**: Restricts boundaries based on scale (e.g., monolith routing vs. bounded contexts).
- **QA Agent**: Escalates QA strategy (e.g., syntax/unit testing for SMALL, performance/security testing for ENTERPRISE).
- **Delivery Agent**: Customizes deployment (e.g., simple Docker containers vs. orchestrated multi-region topologies).
- **Supervisor**: Parallelizes execution for independent modules on LARGE projects but maintains sequential flow for SMALL projects. Dynamically handles `SCALE_CHANGE_DETECTED` events to re-evaluate the architecture mid-flight if requirements change.
