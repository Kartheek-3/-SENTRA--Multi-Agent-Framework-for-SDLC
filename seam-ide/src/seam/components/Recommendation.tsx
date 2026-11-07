import React, { useState } from 'react';

export type RecommendationItem = {
  id: string;
  title: string;
  command: string;
  reason?: string;
};

export type RecommendationProps = {
  recommendations?: RecommendationItem[];
  onRun: (command: string) => void;
};

export function Recommendation({ recommendations, onRun }: RecommendationProps) {
  const [showAll, setShowAll] = useState(false);

  const displayList: RecommendationItem[] = recommendations || [];

  if (displayList.length === 0) {
    return null;
  }

  const primaryRec = displayList[0];
  const remainingCount = displayList.length - 1;

  if (!primaryRec) return null;

  return (
    <div className="agentRecommendationMinimal" role="region" aria-label="Recommendation">
      <div className="recTopRow">
        <span className="sectionTitleSmall">RECOMMENDED</span>
      </div>

      <div className="recContentRow">
        <span className="recTitleText">{primaryRec.title}</span>
        <button
          type="button"
          className="recRunBtnMinimal"
          onClick={() => onRun(primaryRec.command)}
          title={`Run: ${primaryRec.command}`}
        >
          ▶ Run
        </button>
      </div>

      {remainingCount > 0 && !showAll && (
        <button
          type="button"
          className="recMoreTrigger"
          onClick={() => setShowAll(true)}
        >
          +{remainingCount} more suggestions →
        </button>
      )}

      {showAll && (
        <div className="recExpandedList">
          {displayList.slice(1).map(rec => (
            <div key={rec.id} className="recSecondaryRow">
              <span className="recSecondaryTitle">{rec.title}</span>
              <button
                type="button"
                className="recRunBtnSecondary"
                onClick={() => onRun(rec.command)}
              >
                Run
              </button>
            </div>
          ))}
          <button
            type="button"
            className="recMoreTrigger"
            onClick={() => setShowAll(false)}
          >
            Show less ↑
          </button>
        </div>
      )}
    </div>
  );
}
