import React, { useState } from 'react';

export type ToolApprovalRequest = {
  id: string;
  action: string;
  agent: string;
  tool: string;
  target: string;
  risk: 'READ_ONLY' | 'LOW' | 'MEDIUM' | 'HIGH' | 'DESTRUCTIVE';
  reason: string;
  params?: Record<string, any>;
};

export type AgentApprovalCardProps = {
  approval: ToolApprovalRequest | null;
  onApprove: (id: string) => Promise<void> | void;
  onDeny: (id: string) => Promise<void> | void;
};

export function AgentApprovalCard({ approval, onApprove, onDeny }: AgentApprovalCardProps) {
  const [detailsVisible, setDetailsVisible] = useState(false);
  const [processing, setProcessing] = useState(false);

  if (!approval) return null;

  const handleAction = async (isApproved: boolean) => {
    setProcessing(true);
    try {
      if (isApproved) {
        await onApprove(approval.id);
      } else {
        await onDeny(approval.id);
      }
    } finally {
      setProcessing(false);
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'HIGH':
      case 'DESTRUCTIVE':
        return 'riskHigh';
      case 'MEDIUM':
        return 'riskMedium';
      case 'LOW':
      default:
        return 'riskLow';
    }
  };

  return (
    <div className="agentApprovalCard" role="alert" aria-label="Tool Permission Gate">
      <div className="approvalCardHeader">
        <div className="approvalTitleCluster">
          <span className="approvalShieldIcon">🛡️</span>
          <div>
            <strong className="approvalTitle">APPROVAL REQUIRED</strong>
            <span className="approvalSub">Permission Engine Gate Active</span>
          </div>
        </div>
        <span className={`riskBadge ${getRiskColor(approval.risk)} monospace`}>
          RISK: {approval.risk}
        </span>
      </div>

      <div className="approvalDetailsGrid">
        <div className="approvalItem">
          <span className="approvalLabel">ACTION</span>
          <span className="approvalValue monospace">{approval.action}</span>
        </div>
        <div className="approvalItem">
          <span className="approvalLabel">AGENT</span>
          <span className="approvalValue highlight monospace">{approval.agent}</span>
        </div>
        <div className="approvalItem">
          <span className="approvalLabel">TARGET</span>
          <span className="approvalValue monospace" title={approval.target}>
            {approval.target}
          </span>
        </div>
        <div className="approvalItem">
          <span className="approvalLabel">REASON</span>
          <span className="approvalValue">{approval.reason}</span>
        </div>
      </div>

      {detailsVisible && approval.params && (
        <div className="approvalParamsAccordion">
          <span className="paramsLabel">Operation Parameters:</span>
          <pre className="paramsJson monospace">
            {JSON.stringify(approval.params, null, 2)}
          </pre>
        </div>
      )}

      <div className="approvalActionsRow">
        <button
          className="approvalBtn approveBtn"
          onClick={() => handleAction(true)}
          disabled={processing}
          title="Approve this operation and proceed"
        >
          {processing ? 'Processing...' : '✓ APPROVE'}
        </button>

        <button
          className="approvalBtn denyBtn"
          onClick={() => handleAction(false)}
          disabled={processing}
          title="Deny operation and block tool execution"
        >
          ✕ DENY
        </button>

        <button
          className="approvalBtn detailsBtn"
          onClick={() => setDetailsVisible(!detailsVisible)}
          title="Inspect parameter details"
        >
          {detailsVisible ? 'HIDE DETAILS' : 'VIEW DETAILS'}
        </button>
      </div>
    </div>
  );
}
