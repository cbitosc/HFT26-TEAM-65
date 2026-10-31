import React from 'react';

export default function DielActivityChart({ temporal, metrics }) {
  if (!temporal || !metrics) return null;

  const maxSightings = Math.max(...temporal.hourly_distribution.map(h => h.total), 1);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 24-Hour Circular Diel Visualizer */}
        <div className="lg:col-span-2 bg-[#121c17] border border-emerald-900/40 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-base text-slate-100">
                24-Hour Diel Circadian Activity Curve
              </h3>
              <p className="text-xs text-slate-400">Circadian distribution of independent wildlife sightings (00:00 to 23:00)</p>
            </div>
            <div className="flex items-center space-x-3 text-[11px] text-slate-400 font-mono">
              <span className="flex items-center space-x-1"><span class="w-2.5 h-2.5 rounded bg-indigo-500"></span><span>Night</span></span>
              <span className="flex items-center space-x-1"><span class="w-2.5 h-2.5 rounded bg-amber-500"></span><span>Crepuscular</span></span>
              <span className="flex items-center space-x-1"><span class="w-2.5 h-2.5 rounded bg-emerald-500"></span><span>Daylight</span></span>
            </div>
          </div>

          {/* Bar Chart Visualization */}
          <div className="h-64 flex items-end justify-between gap-1.5 pt-8 border-b border-emerald-950 pb-2">
            {temporal.hourly_distribution.map(h => {
              const heightPct = Math.round((h.total / maxSightings) * 100);
              let barColor = 'bg-emerald-500';
              if (h.hour < 5 || h.hour > 20) barColor = 'bg-indigo-500';
              else if ((h.hour >= 5 && h.hour <= 7) || (h.hour >= 18 && h.hour <= 20)) barColor = 'bg-amber-500';

              return (
                <div key={h.hour} className="flex-1 flex flex-col items-center group relative">
                  <div
                    style={{ height: `${Math.max(heightPct, 6)}%` }}
                    className={`w-full rounded-t transition-all group-hover:brightness-125 ${barColor}`}
                  ></div>
                  <span className="text-[9px] font-mono text-slate-400 mt-1">
                    {h.hour % 3 === 0 ? `${h.hour}h` : ''}
                  </span>
                  {/* Tooltip */}
                  <div className="absolute -top-8 px-2 py-1 bg-black text-[10px] rounded text-emerald-300 font-mono whitespace-nowrap opacity-0 group-hover:opacity-100 transition pointer-events-none z-10">
                    {h.hour_label}: {h.total} sightings
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Species Distribution List */}
        <div className="bg-[#121c17] border border-emerald-900/40 rounded-xl p-5 space-y-3">
          <h3 className="font-bold text-base text-slate-100">Species Abundance</h3>
          <p className="text-xs text-slate-400">Independent Sighting Events (burst deduplicated)</p>
          <div className="space-y-2 pt-2">
            {Object.entries(metrics.species_distribution || {}).map(([sp, cnt], idx) => (
              <div key={sp} className="flex items-center justify-between text-xs">
                <span className="capitalize text-slate-300 flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                  <span>{sp.replace('_', ' ')}</span>
                </span>
                <span className="font-mono text-emerald-400 font-bold">{cnt}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Diel Classifications Cards */}
      <div className="bg-[#121c17] border border-emerald-900/40 rounded-xl p-5 space-y-3">
        <h4 className="font-bold text-sm text-slate-200">Species Circadian Niches</h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          {Object.entries(temporal.diel_classifications || {}).map(([sp, d]) => (
            <div key={sp} className="p-3 rounded-lg bg-[#0e1612] border border-emerald-950/80 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="font-bold text-xs text-slate-200 capitalize">{sp.replace('_', ' ')}</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                  {d.category}
                </span>
              </div>
              <div className="grid grid-cols-3 gap-1 text-[10px] text-slate-400 font-mono pt-1">
                <div>Night: <span className="text-slate-200">{d.night_pct}%</span></div>
                <div>Crep: <span className="text-slate-200">{d.crepuscular_pct}%</span></div>
                <div>Day: <span className="text-slate-200">{d.day_pct}%</span></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
