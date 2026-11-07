import React from 'react';

export type VerificationCheck = {
  id: string;
  category: 'TypeScript' | 'Unit Test' | 'API Contract' | 'E2E' | 'Regression';
  status: 'PASS' | 'RUNNING' | 'FAILED' | 'PENDING';
  duration?: string;
  evidence?: string;
  errorDetail?: string;
};

export type AgentVerifyTabProps = {
  checks: VerificationCheck[];
  defectCount: number;
  onStartRepair?: () => void;
  onOpenFailure?: () => void;
  onSelectView?: (view: string) => void;
};

export function AgentVerifyTab({
  checks,
  defectCount,
  onStartRepair,
  onOpenFailure,
  onSelectView,
}: AgentVerifyTabProps) {
  // Default canonical verification suite
  const displayChecks: VerificationCheck[] = checks.length > 0 ? checks : [
    {
      id: 'check-ts',
      category: 'TypeScript',
      status: 'PASS',
      duration: '180 ms',
      evidence: '0 diagnostics across 42 files',
    },
    {
      id: 'check-unit',
      category: 'Unit Test',
      status: 'PASS',
      duration: '320 ms',
      evidence: '14 unit test suites passing',
    },
    {
      id: 'check-contract',
      category: 'API Contract',
      status: 'PASS',
      duration: '95 ms',
      evidence: 'FastAPI / Pydantic v2 schemas synchronized',
    },
    {
      id: 'check-e2e',
      category: 'E2E',
      status: defectCount > 0 ? 'FAILED' : 'PASS',
      duration: '450 ms',
      evidence: defectCount > 0 ? '1 assertion failed in AuthFlow spec' : 'All browser assertions passing',
      errorDetail: defectCount > 0 ? 'AuthContext.tsx line 48: token exchange expected non-null uid' : undefined,
    },
    {
      id: 'check-regression',
      category: 'Regression',
      status: defectCount > 0 ? 'PENDING' : 'PASS',
      duration: defectCount > 0 ? '—' : '210 ms',
      evidence: 'Zero regressions detected across downstream models',
    },
  ];

  const hasFailures = displayChecks.some(c => c.status === 'FAILED') || defectCount > 0;
  const isAllPassed = displayChecks.every(c => c.status === 'PASS') && defectCount === 0;

  const getCheckIcon = (status: VerificationCheck['status']) => {
    switch (status) {
      case 'PASS':
        return <span className="checkIcon pass">✓</span>;
      case 'RUNNING':
        return <span className="checkIcon running pulse">●</span>;
      case 'FAILED':
        return <span className="checkIcon fail">✕</span>;
      case 'PENDING':
      default:
        return <span className="checkIcon pending">○</span>;
    }
  };

  return (
    <div className="agentVerifyContainer" role="tabpanel" aria-label="Targeted Verification Gates">
      {/* 1. High-Level Quality Verdict Card */}
      <div className={`verdictCard ${hasFailures ? 'verdictFail' : 'verdictPass'}`}>
        <div className="verdictHeaderRow">
          <span className="verdictLabel">OVERALL QUALITY GATE</span>
          <span className="verdictBadge monospace">
            {hasFailures ? 'FAILED' : isAllPassed ? 'PASS' : 'IN PROGRESS'}
          </span>
        </div>

        <div className="verdictMetricsRow">
          <div className="verdictMetric">
            <span className="vMetricKey">Targeted Verification:</span>
            <span className={`vMetricVal ${hasFailures ? 'fail' : 'pass'}`}>
              {hasFailures ? 'FAILED' : 'PASS'}
            </span>
          </div>
          <div className="verdictMetric">
            <span className="vMetricKey">Regression:</span>
            <span className="vMetricVal pass">
              {hasFailures ? 'BLOCKED' : 'PASS'}
            </span>
          </div>
          <div className="verdictMetric">
            <span className="vMetricKey">Delivery Gate:</span>
            <span className="vMetricVal monospace">
              {hasFailures ? 'NOT_READY' : 'READY'}
            </span>
          </div>
        </div>

        {/* Failure alert banner */}
        {hasFailures && (
          <div className="verifyFailureBanner">
            <div className="failureTextCluster">
              <span className="failureWarningIcon">⚠️</span>
              <div>
                <strong>Verification Defect Flagged</strong>
                <p>1 or more test checks failed. Defect localization is active.</p>
              </div>
            </div>
            <div className="failureActionCluster">
              <button
                type="button"
                className="verifyActionBtn failureBtn"
                onClick={onOpenFailure}
              >
                Open Failure
              </button>
              <button
                type="button"
                className="verifyActionBtn repairBtn"
                onClick={onStartRepair}
              >
                ⚡ Start Repair
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 2. Checks Breakdown Checklist */}
      <div className="verifyChecklist">
        <div className="checklistHeader">
          <span className="checklistTitle">TARGETED VERIFICATION CHECKS</span>
          <span className="checklistCount monospace">
            {displayChecks.filter(c => c.status === 'PASS').length} / {displayChecks.length} PASSING
          </span>
        </div>

        <div className="checksList">
          {displayChecks.map(check => (
            <div key={check.id} className={`checkRow ${check.status.toLowerCase()}`}>
              <div className="checkIconCol">
                {getCheckIcon(check.status)}
              </div>

              <div className="checkDetailsCol">
                <div className="checkCategoryRow">
                  <strong className="checkCategoryName">{check.category}</strong>
                  <span className={`checkStatusTag ${check.status.toLowerCase()} monospace`}>
                    {check.status}
                  </span>
                </div>

                <div className="checkEvidenceRow">
                  {check.evidence && (
                    <span className="checkEvidenceText monospace">{check.evidence}</span>
                  )}
                  {check.duration && (
                    <span className="checkDuration monospace">⏱ {check.duration}</span>
                  )}
                </div>

                {check.errorDetail && (
                  <div className="checkErrorDetail monospace">
                    {check.errorDetail}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
