import React from 'react';

export type ExpandableSectionProps = {
  title: string;
  badge?: string | number;
  badgeColor?: 'default' | 'accent' | 'success' | 'warn' | 'error';
  isExpanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
};

export function ExpandableSection({
  title,
  badge,
  badgeColor = 'default',
  isExpanded,
  onToggle,
  children,
}: ExpandableSectionProps) {
  return (
    <div className={`agentExpandableSection ${isExpanded ? 'expanded' : 'collapsed'}`}>
      <button
        type="button"
        className="expandableSectionHeader"
        onClick={onToggle}
        aria-expanded={isExpanded}
        title={`${isExpanded ? 'Collapse' : 'Expand'} ${title}`}
      >
        <div className="sectionHeaderLeft">
          <span className="sectionHeaderTitle">{title}</span>
          {badge !== undefined && badge !== null && (
            <span className={`sectionHeaderBadge badge-${badgeColor} monospace`}>
              {badge}
            </span>
          )}
        </div>

        <span className="sectionChevron monospace" aria-hidden="true">
          {isExpanded ? '▾' : '›'}
        </span>
      </button>

      {isExpanded && (
        <div className="expandableSectionBody">
          {children}
        </div>
      )}
    </div>
  );
}
