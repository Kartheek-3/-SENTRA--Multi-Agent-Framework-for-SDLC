import React, { useState } from 'react';

export type AgentContextCardProps = {
  projectName?: string;
  gitBranch?: string;
  modelName?: string;
  provider?: string;
  hardwareProfile?: string;
  domainName?: string;
  ragCount?: number;
  toolsCount?: number;
  permissions?: string;
  runtime?: string;
  modelFallback?: {
    requested: string;
    actual: string;
    reason: string;
  } | null;
  onOpenContextViewer?: () => void;
};

export function AgentContextCard({
  projectName = 'SEAM Workspace',
  gitBranch = 'final-validation',
  modelName = 'qwen3:4b',
  provider = 'Docker Model Runner',
  hardwareProfile = 'LOW_RESOURCE_CPU',
  domainName = 'Software Engineering',
  ragCount = 5,
  toolsCount = 39,
  permissions = 'SANDBOXED',
  runtime = 'LOCAL / DMR',
  modelFallback = null,
  onOpenContextViewer,
}: AgentContextCardProps) {
  const [contextDetailsOpen, setContextDetailsOpen] = useState(false);

  return (
    <div className="agentContextSection" role="region" aria-label="System & Domain Context">
      {/* 1. Model Fallback Banner if applicable */}
      {modelFallback && (
        <div className="modelFallbackAlert">
          <div className="fallbackHeader">
            <span className="fallbackIcon">⚠️</span>
            <strong>MODEL FALLBACK ACTIVE</strong>
          </div>
          <div className="fallbackDetails monospace">
            <div>Requested: <span>{modelFallback.requested}</span></div>
            <div>Using: <span className="highlight">{modelFallback.actual}</span></div>
            <div>Reason: <span>{modelFallback.reason}</span></div>
          </div>
        </div>
      )}

      {/* 2. System Context Grid */}
      <div className="systemContextCard">
        <div className="contextCardHeader">
          <span className="contextHeaderTitle">RUNTIME & SECURITY CONTEXT</span>
          <span className="contextStatusPill live">ACTIVE</span>
        </div>

        <div className="contextGrid">
          <div className="contextGridItem">
            <span className="cKey">PROJECT</span>
            <span className="cVal" title={projectName}>{projectName}</span>
          </div>
          <div className="contextGridItem">
            <span className="cKey">BRANCH</span>
            <span className="cVal monospace">{gitBranch}</span>
          </div>
          <div className="contextGridItem">
            <span className="cKey">MODEL</span>
            <span className="cVal monospace highlight">{modelName}</span>
          </div>
          <div className="contextGridItem">
            <span className="cKey">HARDWARE</span>
            <span className="cVal monospace">{hardwareProfile}</span>
          </div>
          <div className="contextGridItem">
            <span className="cKey">RAG STATUS</span>
            <span className="cVal success">ACTIVE ({ragCount} docs)</span>
          </div>
          <div className="contextGridItem">
            <span className="cKey">TOOLS</span>
            <span className="cVal monospace">{toolsCount} registered</span>
          </div>
          <div className="contextGridItem">
            <span className="cKey">PERMISSIONS</span>
            <span className="cVal highlight">{permissions}</span>
          </div>
          <div className="contextGridItem">
            <span className="cKey">RUNTIME</span>
            <span className="cVal monospace">{runtime}</span>
          </div>
        </div>
      </div>

      {/* 3. Domain Intelligence Card */}
      <div className="domainIntelligenceCard">
        <div className="domainCardHeader">
          <div className="domainTitleCluster">
            <span className="domainIcon">🧠</span>
            <div>
              <strong>DOMAIN INTELLIGENCE</strong>
              <span className="domainTag">{domainName}</span>
            </div>
          </div>
          <button
            type="button"
            className="viewContextBtn"
            onClick={() => {
              if (onOpenContextViewer) {
                onOpenContextViewer();
              } else {
                setContextDetailsOpen(!contextDetailsOpen);
              }
            }}
          >
            {contextDetailsOpen ? 'HIDE CONTEXT' : 'VIEW CONTEXT'}
          </button>
        </div>

        <div className="domainSourcesSummary">
          <div className="sourceItem">
            <span className="sourceDot pass" />
            <span>Official Language & Framework Specs</span>
          </div>
          <div className="sourceItem">
            <span className="sourceDot pass" />
            <span>Validated Project Architecture Knowledge</span>
          </div>
          <div className="sourceItem">
            <span className="sourceDot pass" />
            <span>ChromaDB Vector Embeddings (FastEmbed BAAI/bge-small-en-v1.5)</span>
          </div>
        </div>

        {contextDetailsOpen && (
          <div className="domainContextAccordion monospace">
            <div className="accordionHeader">RETRIEVED CONTEXT DOCUMENTS ({ragCount}):</div>
            <ul className="retrievedDocsList">
              <li>📄 seam_knowledge/domain_spec.md (Score: 0.94)</li>
              <li>📄 seam_knowledge/api_contract_policy.md (Score: 0.91)</li>
              <li>📄 seam_knowledge/repair_loop_guidelines.md (Score: 0.88)</li>
              <li>📄 seam_knowledge/security_sandbox_rules.md (Score: 0.87)</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
