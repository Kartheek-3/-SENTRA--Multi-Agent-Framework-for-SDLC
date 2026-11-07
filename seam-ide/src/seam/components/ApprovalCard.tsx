import React from 'react';

export type ApprovalRequest = {
  id: string;
  action: string;
  risk: 'LOW' | 'MEDIUM' | 'HIGH';
  agent?: string;
  reason?: string;
  target?: string;
};

export type ApprovalCardProps = {
  request: ApprovalRequest | null;
  onApprove: (id: string) => void;
  onDeny: (id: string) => void;
  onViewDetails?: (req: ApprovalRequest) => void;
};

export function ApprovalCard({ request, onApprove, onDeny, onViewDetails }: ApprovalCardProps) {
  if (!request) return null;

  return (
    <div className="agentApprovalCardMinimal" role="alert" aria-label="Tool Permission Required">
      <div className="approvalCardTop">
        <span className="approvalBadgeLabel">APPROVAL REQUIRED</span>
        <span className={`approvalRiskTag risk-${request.risk.toLowerCase()} monospace`}>
          {request.risk}
        </span>
      </div>

      <div className="approvalActionText monospace">
        {request.action}
      </div>

      <div className="approvalMetaGrid monospace">
        {request.agent && (
          <div className="approvalMetaRow">
            <span className="metaLabel">Agent:</span>
            <span className="metaVal">{request.agent}</span>
          </div>
        )}
        {request.target && (
          <div className="approvalMetaRow">
            <span className="metaLabel">Target:</span>
            <span className="metaVal">{request.target}</span>
          </div>
        )}
        {request.reason && (
          <div className="approvalMetaReason">
            {request.reason}
          </div>
        )}
      </div>

      <div className="approvalButtonsRow">
        <button
          type="button"
          className="approvalBtnMinimal approve"
          onClick={() => onApprove(request.id)}
        >
          ✓ Approve
        </button>
        <button
          type="button"
          className="approvalBtnMinimal deny"
          onClick={() => onDeny(request.id)}
        >
          ✕ Deny
        </button>
        {onViewDetails && (
          <button
            type="button"
            className="approvalBtnMinimal details"
            onClick={() => onViewDetails(request)}
          >
            Details →
          </button>
        )}
      </div>
    </div>
  );
}
