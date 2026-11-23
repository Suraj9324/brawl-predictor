export function SkeletonBlock({
  className = "",
  style,
}: {
  className?: string;
  style?: React.CSSProperties;
}) {
  return (
    <div
      className={`rounded skeleton-shimmer animate-shimmer ${className}`}
      style={style}
    />
  );
}

export function SkeletonCard() {
  return (
    <div className="rounded-2xl border border-line/40 bg-surface-1 p-6">
      <SkeletonBlock className="mb-3 h-3 w-20" />
      <SkeletonBlock className="mb-2 h-7 w-28" />
      <SkeletonBlock className="h-3 w-16" />
    </div>
  );
}

export function SkeletonRow() {
  return (
    <div className="flex items-center gap-4 border-b border-line/40 py-4">
      <SkeletonBlock className="h-8 w-8 rounded-full" />
      <div className="flex-1 space-y-2">
        <SkeletonBlock className="h-4 w-40" />
        <SkeletonBlock className="h-3 w-28" />
      </div>
      <SkeletonBlock className="h-5 w-16" />
    </div>
  );
}

export function SkeletonChart() {
  return (
    <div className="rounded-2xl border border-line/40 bg-surface-1 p-6">
      <SkeletonBlock className="mb-4 h-4 w-32" />
      <div className="flex items-end gap-2">
        {[60, 80, 45, 90, 55, 70, 85, 40, 75, 65].map((h, i) => (
          <SkeletonBlock
            key={i}
            className="flex-1"
            style={{ height: `${h}%`, minHeight: `${h * 1.5}px` } as React.CSSProperties}
          />
        ))}
      </div>
    </div>
  );
}
