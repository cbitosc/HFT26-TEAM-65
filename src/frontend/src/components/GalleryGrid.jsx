import React, { useState, useEffect } from 'react';

export default function GalleryGrid() {
  const [records, setRecords] = useState([]);
  const [total, setTotal] = useState(0);
  const [selectedSpecies, setSelectedSpecies] = useState('');
  const [selectedLocation, setSelectedLocation] = useState('');
  const [includeEmpty, setIncludeEmpty] = useState(true);
  const [alertsOnly, setAlertsOnly] = useState(false);
  const [dedupBursts, setDedupBursts] = useState(false);
  const [activeInspector, setActiveInspector] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [loadingExplain, setLoadingExplain] = useState(false);

  const loadImages = async () => {
    let url = `/api/dataset/images?include_empty=${includeEmpty}&limit=48`;
    if (selectedSpecies) url += `&species=${selectedSpecies}`;
    if (selectedLocation) url += `&locations=${selectedLocation}`;
    if (alertsOnly) url += `&alerts_only=true`;
    if (dedupBursts) url += `&deduplicate_bursts=true`;

    try {
      const res = await fetch(url);
      const data = await res.json();
      setRecords(data.records);
      setTotal(data.total);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadImages();
  }, [selectedSpecies, selectedLocation, includeEmpty, alertsOnly, dedupBursts]);

  const explainRecord = async (rec) => {
    setLoadingExplain(true);
    setExplanation(null);
    try {
      const isNight = rec.datetime && (parseInt(rec.datetime.slice(11, 13)) < 6 || parseInt(rec.datetime.slice(11, 13)) >= 19);
      const res = await fetch('/api/featherless/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          species: rec.species,
          confidence: rec.confidence,
          uncertainty_flags: rec.uncertainty_flags,
          bbox: {
            ymin: rec.bbox ? rec.bbox[0] : 0,
            xmin: rec.bbox ? rec.bbox[1] : 0,
            ymax: rec.bbox ? rec.bbox[2] : 1,
            xmax: rec.bbox ? rec.bbox[3] : 1,
          },
          is_night: isNight
        })
      });
      const data = await res.json();
      setExplanation(data.explanation);
    } catch (e) {
      setExplanation('Failed to generate explanation: ' + e.message);
    } finally {
      setLoadingExplain(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Controls Bar */}
      <div className="bg-[#121c17] border border-emerald-900/40 rounded-xl p-4 flex flex-wrap gap-4 items-center justify-between text-xs">
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={selectedSpecies}
            onChange={(e) => setSelectedSpecies(e.target.value)}
            className="bg-[#0e1612] border border-emerald-900/60 text-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none"
          >
            <option value="">All Species</option>
            <option value="coyote">Coyote</option>
            <option value="bobcat">Bobcat</option>
            <option value="mule_deer">Mule Deer</option>
            <option value="opossum">Opossum</option>
            <option value="raccoon">Raccoon</option>
            <option value="mountain_lion">Mountain Lion</option>
            <option value="gray_fox">Gray Fox</option>
            <option value="striped_skunk">Striped Skunk</option>
            <option value="cottontail_rabbit">Cottontail Rabbit</option>
            <option value="bird">Avian Fauna</option>
          </select>

          <select
            value={selectedLocation}
            onChange={(e) => setSelectedLocation(e.target.value)}
            className="bg-[#0e1612] border border-emerald-900/60 text-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none"
          >
            <option value="">All Stations</option>
            <option value="loc_01">loc_01: Riparian Arroyo</option>
            <option value="loc_02">loc_02: Chaparral Ridge</option>
            <option value="loc_03">loc_03: Oaks Waterhole</option>
            <option value="loc_04">loc_04: Canyon Creek</option>
            <option value="loc_05">loc_05: Grassland Basin</option>
          </select>

          <label className="flex items-center space-x-2 cursor-pointer bg-[#0e1612] px-3 py-1.5 rounded-lg border border-emerald-900/60 text-slate-300">
            <input
              type="checkbox"
              checked={includeEmpty}
              onChange={(e) => setIncludeEmpty(e.target.checked)}
              className="accent-emerald-500"
            />
            <span>Include Empty Frames</span>
          </label>

          <label className="flex items-center space-x-2 cursor-pointer bg-[#1a0a0a] px-3 py-1.5 rounded-lg border border-red-900/60 text-red-300 hover:border-red-500/80 transition">
            <input
              type="checkbox"
              checked={alertsOnly}
              onChange={(e) => setAlertsOnly(e.target.checked)}
              className="accent-red-500"
            />
            <span className="font-bold flex items-center gap-1"><span>🚨</span> Alerts Only (Rare / Dangerous)</span>
          </label>

          <label className="flex items-center space-x-2 cursor-pointer bg-[#0a1714] px-3 py-1.5 rounded-lg border border-teal-800/60 text-teal-300 hover:border-teal-400 transition" title="Hide redundant burst sequence frames and show unique encounters">
            <input
              type="checkbox"
              checked={dedupBursts}
              onChange={(e) => setDedupBursts(e.target.checked)}
              className="accent-teal-500"
            />
            <span className="font-bold flex items-center gap-1"><span>🔄</span> Collapse Duplicates</span>
          </label>
        </div>

        <div className="text-slate-400 font-mono text-[11px]">
          Showing {records.length} of {total} frames
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {records.map((rec) => {
          const isAlert = rec.is_rare || rec.is_dangerous || (rec.alert && rec.alert.has_alert);
          return (
            <div
              key={rec.id}
              onClick={() => {
                setActiveInspector(rec);
                setExplanation(null);
              }}
              className={`group cursor-pointer rounded-xl overflow-hidden shadow-sm transition ${
                isAlert
                  ? 'bg-[#180b0b] border-2 border-red-500/80 hover:border-red-400 ring-2 ring-red-500/20'
                  : 'bg-[#0e1612] border border-emerald-950/80 hover:border-emerald-500/60'
              }`}
            >
              <div className="h-44 bg-black relative overflow-hidden">
                <img
                  src={rec.image_url}
                  alt={rec.species}
                  className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                  loading="lazy"
                />
                <div className="absolute top-2 left-2 flex flex-col space-y-1">
                  <span className="bg-black/75 px-2 py-0.5 rounded text-[10px] font-mono text-slate-300">
                    {rec.location}
                  </span>
                  {isAlert && (
                    <span className="bg-red-950/90 border border-red-500 text-red-300 font-extrabold px-2 py-0.5 rounded text-[10px] font-mono animate-pulse">
                      🚨 {rec.is_dangerous ? 'DANGEROUS' : 'RARE'}
                    </span>
                  )}
                  {rec.is_empty && (
                    <span className="bg-black/75 px-2 py-0.5 rounded text-[10px] font-mono text-rose-400">
                      EMPTY
                    </span>
                  )}
                </div>
                <div className="absolute bottom-2 right-2 bg-black/75 px-2 py-0.5 rounded text-[10px] font-mono text-emerald-400 font-bold">
                  {Math.round(rec.confidence * 100)}% Conf
                </div>
              </div>

              <div className="p-3">
                <div className="flex items-center justify-between">
                  <h4 className={`font-bold text-xs capitalize ${isAlert ? 'text-red-300' : 'text-slate-200'}`}>
                    {rec.species.replace('_', ' ')}
                  </h4>
                  <span className="text-[10px] font-mono text-slate-400">
                    {rec.datetime.slice(11, 16)}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal Inspector */}
      {activeInspector && (
        <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#101814] border border-emerald-800/60 rounded-2xl max-w-2xl w-full p-5 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-emerald-950 pb-2">
              <h3 className="font-bold text-sm text-white">
                Inspection: {activeInspector.id} ({activeInspector.location})
              </h3>
              <button
                onClick={() => setActiveInspector(null)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            {/* RARE / DANGEROUS ALERT IN INSPECTOR */}
            {(activeInspector.is_rare || activeInspector.is_dangerous || (activeInspector.alert && activeInspector.alert.has_alert)) && (
              <div className="p-3.5 rounded-xl bg-gradient-to-r from-red-950/90 via-[#260505] to-amber-950/80 border-2 border-red-500 shadow-md space-y-1.5 text-xs text-red-200 text-left">
                <div className="flex items-center justify-between">
                  <span className="font-extrabold text-red-200 flex items-center gap-1.5 uppercase tracking-wide text-xs">
                    <span>🚨</span> {activeInspector.alert?.badge || (activeInspector.is_dangerous ? 'DANGEROUS WILDLIFE ALERT' : 'RARE SPECIES SIGHTING')}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-red-600 text-white uppercase">
                    {activeInspector.alert?.alert_level || 'CRITICAL'}
                  </span>
                </div>
                <p className="font-bold text-white text-xs">
                  {activeInspector.alert?.title || `${activeInspector.common_name || activeInspector.species} Alert`}
                </p>
                <p className="text-[11px] text-red-100">
                  {activeInspector.alert?.message || 'High priority wildlife detection requiring researcher & ranger awareness.'}
                </p>
                <div className="text-[10px] text-amber-300 italic pt-1 border-t border-red-900/60">
                  <strong>Protocol:</strong> {activeInspector.alert?.safety_protocol || 'Maintain safe standoff distance and log coordinates.'}
                </div>
              </div>
            )}

            <div className="relative bg-black rounded-xl overflow-hidden flex items-center justify-center max-h-72">
              <img
                src={activeInspector.image_url}
                alt={activeInspector.species}
                className="max-h-72 object-contain"
              />
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800/40">
                <div className="text-[10px] uppercase font-bold text-emerald-400">Species</div>
                <div className="font-bold text-white capitalize mt-0.5">
                  {activeInspector.species.replace('_', ' ')}
                </div>
              </div>
              <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800/40">
                <div className="text-[10px] uppercase font-bold text-emerald-400">Confidence</div>
                <div className="font-bold text-white mt-0.5 font-mono">
                  {Math.round(activeInspector.confidence * 100)}%
                </div>
              </div>
            </div>

            {explanation && (
              <div className="p-3 rounded-xl bg-black border border-emerald-950 text-xs text-slate-300">
                <strong className="text-emerald-400 block mb-1">Featherless AI Rationale:</strong>
                {explanation}
              </div>
            )}

            <button
              onClick={() => explainRecord(activeInspector)}
              disabled={loadingExplain}
              className="w-full py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-black font-bold text-xs"
            >
              {loadingExplain ? 'Explaining...' : 'Explain Detection with Featherless AI'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
