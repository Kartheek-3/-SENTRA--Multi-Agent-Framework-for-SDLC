import React from 'react';

export type BreadcrumbBarProps = {
  path: string;
  onNavigateSegment?: (segmentPath: string) => void;
};

export function BreadcrumbBar({ path, onNavigateSegment }: BreadcrumbBarProps) {
  if (!path) {
    return (
      <div className="breadcrumbBar" aria-label="Breadcrumb navigation">
        <span className="breadcrumbItem root">workspace</span>
      </div>
    );
  }

  const segments = path.split('/').filter(Boolean);
  const fileName = segments[segments.length - 1] || '';
  const isComponent = fileName.endsWith('.tsx') || fileName.endsWith('.jsx');
  const componentName = isComponent ? fileName.replace(/\.[^/.]+$/, '') : null;

  // Build cumulative paths
  let cumulative = '';
  const items = segments.map((seg, idx) => {
    cumulative = cumulative ? `${cumulative}/${seg}` : seg;
    const isLast = idx === segments.length - 1;
    return {
      name: seg,
      fullPath: cumulative,
      isLast,
      isFolder: !isLast,
    };
  });

  return (
    <div className="breadcrumbBar" aria-label="Breadcrumb navigation">
      {items.map((item, idx) => (
        <React.Fragment key={`${item.fullPath}-${idx}`}>
          <button
            className={`breadcrumbItem ${item.isLast ? 'active' : ''}`}
            onClick={() => onNavigateSegment?.(item.fullPath)}
            title={item.fullPath}
          >
            {item.isLast && isComponent && (
              <span className="breadcrumbIcon react" aria-hidden="true">⚛</span>
            )}
            {item.isFolder && (
              <span className="breadcrumbIcon folder" aria-hidden="true">📁</span>
            )}
            <span className="breadcrumbText">{item.name}</span>
          </button>

          {(idx < items.length - 1 || componentName) && (
            <span className="breadcrumbSeparator" aria-hidden="true">›</span>
          )}
        </React.Fragment>
      ))}

      {/* Symbol item if component */}
      {componentName && (
        <span className="breadcrumbItem symbol" title={`Component: ${componentName}`}>
          <span className="breadcrumbSymbolIcon" aria-hidden="true">ƒ</span>
          <span className="breadcrumbText">{componentName}</span>
        </span>
      )}
    </div>
  );
}
