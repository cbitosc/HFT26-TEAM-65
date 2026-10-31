import React from 'react';

export default function SpatialMap({ spatial }) {
  if (!spatial) return null;

  return (
    <div className="bg-[#121c17] border border-emerald-900/40 rounded-xl p-5 space-y-4">
      <div>
        <h3 className="font-bold text-base text-slate-100">
          Monitored Camera Trap Stations (Southwestern Ecological Network)
        </h3>
        <p className="text-xs text-slate-400">
          Encounter volumes, false-trigger rates, and dominant wildlife per deployment site
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {spatial.stations.map((st) => (
          <div key={st.location_id} className="p-4 rounded-xl bg-[#0e1612] border border-emerald-950/80 space-y-2">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[10px] font-mono text-emerald-400 uppercase font-bold">
                  {st.location_id}
                </span>
                <h4 className="font-bold text-xs text-slate-200 mt-0.5">{st.name}</h4>
              </div>
              <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 text-[10px] font-mono font-bold">
                {st.wildlife_events} events
              </span>
            </div>
            <p className="text-[11px] text-slate-400">{st.habitat}</p>
            <div className="border-t border-emerald-950/60 pt-2 grid grid-cols-2 gap-1 text-[10px] text-slate-400 font-mono">
              <div>Total: <span className="text-slate-200">{st.total_images}</span></div>
              <div>Empty: <span className="text-slate-200">{st.empty_rate_pct}%</span></div>
              <div className="col-span-2">
                Dominant: <span className="text-emerald-400 capitalize">{st.dominant_species.replace('_', ' ')}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
