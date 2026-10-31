import React from 'react';

export default function KPICards({ metrics }) {
  if (!metrics) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3.5 animate-pulse">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="h-24 bg-[#121c17] rounded-xl border border-emerald-950"></div>
        ))}
      </div>
    );
  }

  const items = [
    { label: 'Ingested Frames', val: metrics.total_images.toLocaleString(), sub: 'Caltech Camera Traps', color: 'text-white' },
    { label: 'Empty Filtered', val: `${metrics.empty_rate_pct}%`, sub: `${metrics.empty_count} frames removed`, color: 'text-emerald-400' },
    { label: 'Time Saved', val: `${metrics.hours_saved} hrs`, sub: '@ 4.5s manual review', color: 'text-teal-300' },
    { label: 'Species Richness', val: metrics.species_richness, sub: 'Distinct taxa identified', color: 'text-amber-300' },
    { label: 'Shannon Index (H\')', val: metrics.shannon_diversity_index.toFixed(2), sub: `Evenness J': ${metrics.pielou_evenness.toFixed(2)}`, color: 'text-cyan-300' },
    { label: 'Review Flagged', val: metrics.review_required_count, sub: 'Low conf / IR blur', color: 'text-rose-300' },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
      {items.map((it, i) => (
        <div key={i} className="bg-[#121c17] border border-emerald-900/40 rounded-xl p-4 shadow-sm">
          <span className="text-xs font-medium text-slate-400">{it.label}</span>
          <div className={`text-2xl font-bold mt-1 ${it.color}`}>{it.val}</div>
          <div className="text-[11px] text-slate-500 mt-1">{it.sub}</div>
        </div>
      ))}
    </div>
  );
}
