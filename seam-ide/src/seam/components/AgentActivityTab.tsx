import React, { useRef, useEffect } from 'react';
import { ChatMessage } from '../chatTypes';

export type AgentActivityTabProps = {
  events: any[];
  messages: ChatMessage[];
  onOpenFile?: (path: string) => void;
};

export function AgentActivityTab({ events, messages, onOpenFile }: AgentActivityTabProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new event
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events.length, messages.length]);

  // Merge real events and messages into unified structured activity entries
  const activityItems = React.useMemo(() => {
    const list: Array<{
      id: string;
      time: string;
      agent: string;
      type: string;
      summary: string;
      status?: string;
      targetPath?: string;
      severity?: string;
      details?: any;
    }> = [];

    // Map EventStore events
    (events || []).forEach((ev, idx) => {
      const timeStr = ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : 'LIVE';
      const agentName = ev.agent || 'SUPERVISOR';
      const summary = ev.summary || ev.operation || ev.event || 'Workflow update';
      list.push({
        id: ev.event_id || `ev-${idx}`,
        time: timeStr,
        agent: agentName,
        type: ev.event || 'EVENT',
        summary,
        status: ev.status,
        targetPath: ev.path,
        details: ev,
      });
    });

    // Map chat/agent messages
    (messages || []).forEach((msg, idx) => {
      const timeStr = msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : 'LIVE';
      const agentName = msg.agent || (msg.role === 'USER' ? 'ENGINEER' : 'SUPERVISOR');
      list.push({
        id: msg.id || `msg-${idx}`,
        time: timeStr,
        agent: agentName,
        type: msg.type || 'ACTIVITY',
        summary: msg.content,
        status: msg.status,
        targetPath: msg.artifact?.path,
        severity: msg.severity,
      });
    });

    // Sort by timestamp if available or keep stream order
    return list;
  }, [events, messages]);

  const getAgentColorClass = (agent: string) => {
    const normalized = agent.toLowerCase();
    if (normalized.includes('analysis')) return 'agentAnalysis';
    if (normalized.includes('plan')) return 'agentPlanning';
    if (normalized.includes('supervisor')) return 'agentSupervisor';
    if (normalized.includes('coding')) return 'agentCoding';
    if (normalized.includes('qa')) return 'agentQA';
    if (normalized.includes('delivery')) return 'agentDelivery';
    return 'agentDefault';
  };

  return (
    <div className="agentActivityStream" role="tabpanel" aria-label="Live Agent Activity Stream">
      <div className="activityStreamHeader">
        <span className="streamHeaderTitle">AUTONOMOUS ENGINEERING STREAM</span>
        <span className="streamHeaderCount monospace">
          {activityItems.length} EVENTS RECORDED
        </span>
      </div>

      <div className="activityList scrollArea">
        {activityItems.length === 0 ? (
          <div className="emptyActivityNotice">
            <span className="emptyNoticeGlyph">⚡</span>
            <h4>Stream Standing By</h4>
            <p>Live agent activities, file modifications, and test executions will stream here in real time.</p>
          </div>
        ) : (
          activityItems.map(item => (
            <div key={item.id} className="activityEventRow">
              <div className="eventTimestamp monospace">{item.time}</div>

              <div className="eventAgentBadgeCol">
                <span className={`eventAgentBadge ${getAgentColorClass(item.agent)} monospace`}>
                  {item.agent.toUpperCase()}
                </span>
              </div>

              <div className="eventPayloadCol">
                <div className="eventSummaryText">{item.summary}</div>

                {item.targetPath && (
                  <div className="eventTargetRow">
                    <button
                      type="button"
                      className="eventTargetFile monospace"
                      onClick={() => onOpenFile?.(item.targetPath!)}
                      title={`Open ${item.targetPath} in editor`}
                    >
                      📄 {item.targetPath}
                    </button>
                  </div>
                )}

                {item.status && (
                  <span className={`eventStatusPill ${(item.status || '').toLowerCase()}`}>
                    {item.status}
                  </span>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
