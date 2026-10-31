import React, { useState } from 'react';

export default function UploadModal({ onClose, onSuccess }) {
  const [files, setFiles] = useState([]);
  const [station, setStation] = useState('loc_01');
  const [loading, setLoading] = useState(false);
  const [batchResult, setBatchResult] = useState(null);

  const handleUpload = async () => {
    if (!files || files.length === 0) return;
    setLoading(true);
    setBatchResult(null);

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }
    formData.append('location', station);

    try {
      const res = await fetch('/api/detection/predict-batch', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      setBatchResult(data);
      if (onSuccess) onSuccess(data);

      // Automatically trigger Excel file export download
      downloadExcel(data);
    } catch (e) {
      alert('Upload failed: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadExcel = async (dataToExport) => {
    const data = dataToExport || batchResult;
    if (!data || !data.items || data.items.length === 0) return;

    try {
      const payload = {
        items: data.items,
        location: data.location || station,
        timestamp: data.timestamp || new Date().toISOString().replace('T', ' ').slice(0, 19)
      };
      const res = await fetch('/api/detection/export-batch-excel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error('Failed to download Excel file');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const ts = (payload.timestamp || '').replace(/[: ]/g, '-');
      a.download = `wildlife_batch_counts_${ts}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => window.URL.revokeObjectURL(url), 2000);
    } catch (err) {
      alert('Error exporting Excel: ' + err.message);
    }
  };

  // Group species counts
  const speciesCounts = {};
  if (batchResult && batchResult.items) {
    batchResult.items.forEach((item) => {
      if (!item.is_empty) {
        const name = item.common_name || item.species || 'Unknown';
        speciesCounts[name] = (speciesCounts[name] || 0) + 1;
      }
    });
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#101814] border border-emerald-800/60 rounded-2xl max-w-xl w-full p-5 space-y-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center border-b border-emerald-950 pb-2">
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-sm text-white">Upload Camera Trap Frames (Multi-Upload)</h3>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/20 text-emerald-400 font-bold">EXCEL EXPORT</span>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white">✕</button>
        </div>

        <div className="space-y-3 text-xs">
          <div>
            <label className="block text-slate-400 mb-1">Select Images (Multiple supported):</label>
            <input
              type="file"
              accept="image/*"
              multiple
              onChange={(e) => setFiles(Array.from(e.target.files))}
              className="w-full text-slate-300 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-emerald-600 file:text-black hover:file:bg-emerald-500"
            />
            {files.length > 0 && (
              <p className="mt-1 text-[11px] text-emerald-400 font-mono">
                ✓ {files.length} photo{files.length > 1 ? 's' : ''} selected
              </p>
            )}
          </div>

          <div>
            <label className="block text-slate-400 mb-1">Camera Station:</label>
            <select
              value={station}
              onChange={(e) => setStation(e.target.value)}
              className="w-full bg-[#0a0f0d] border border-emerald-900/60 rounded-lg p-2 text-slate-200"
            >
              <option value="loc_01">loc_01: Riparian Arroyo</option>
              <option value="loc_02">loc_02: Chaparral Ridge</option>
              <option value="loc_03">loc_03: Oaks Waterhole</option>
              <option value="loc_04">loc_04: Canyon Creek</option>
              <option value="loc_05">loc_05: Grassland Basin</option>
            </select>
          </div>
        </div>

        {batchResult && (
          <div className="p-4 rounded-xl bg-black border border-emerald-900/80 text-xs space-y-3">
            {/* RARE & DANGEROUS ANIMAL ALERT */}
            {(batchResult.has_alerts || (batchResult.items && batchResult.items.some(it => it.is_rare || it.is_dangerous))) && (
              <div className="p-3.5 rounded-xl bg-gradient-to-r from-red-950/95 via-[#2b0808] to-amber-950/90 border-2 border-red-500 shadow-lg space-y-2 text-left">
                <div className="flex items-center justify-between">
                  <span className="font-extrabold text-xs text-red-200 flex items-center gap-1.5 uppercase tracking-wide">
                    <span>🚨</span> RARE & DANGEROUS ANIMAL ALERT!
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-red-600 text-white uppercase shadow-sm">
                    CRITICAL THREAT
                  </span>
                </div>
                <p className="text-[11px] text-red-100 font-medium leading-relaxed">
                  {batchResult.alert_summary?.headline || 'Rare or dangerous wildlife detected in this uploaded batch.'}
                </p>
                {batchResult.alert_summary?.alert_species && batchResult.alert_summary.alert_species.length > 0 && (
                  <div className="text-[11px] text-red-300 font-mono">
                    Species Flagged: <strong className="text-white">{batchResult.alert_summary.alert_species.join(', ')}</strong>
                  </div>
                )}
                <div className="text-[10px] text-amber-300 italic pt-1 border-t border-red-900/60">
                  Ranger Advisory: Alert perimeter field patrols, maintain 150m standoff distance, and verify livestock enclosures.
                </div>
              </div>
            )}

            {/* Smart Deduplication & Sighting Summary */}
            {batchResult.duplicate_summary && batchResult.duplicate_summary.duplicate_images_count > 0 && (
              <div className="p-3 rounded-xl bg-teal-950/60 border border-teal-500/50 space-y-1 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-extrabold text-teal-300 text-[11px] flex items-center gap-1.5 uppercase tracking-wide">
                    <span>🔄</span> Smart Sighting Deduplication
                  </span>
                  <span className="px-2 py-0.5 rounded text-[9px] font-mono font-extrabold bg-teal-400 text-black">
                    {batchResult.duplicate_summary.workload_reduction_pct}% REVIEW WORK SAVED
                  </span>
                </div>
                <p className="text-[11px] text-slate-200">
                  Grouped <b>{batchResult.duplicate_summary.total_images}</b> photos into <b>{batchResult.duplicate_summary.unique_encounters_count}</b> wildlife encounters ({batchResult.duplicate_summary.duplicate_images_count} redundant burst frames eliminated).
                </p>
              </div>
            )}

            <div className="flex justify-between items-center border-b border-emerald-950 pb-2">
              <div className="font-bold text-emerald-400">
                Batch Processed: {batchResult.total_processed} Images
              </div>
              <div className="text-[11px] font-mono text-slate-400">
                ⏱ {batchResult.timestamp}
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="p-2 rounded bg-[#0e1612] border border-emerald-950">
                <div className="text-[10px] text-slate-400 uppercase">Animals Found</div>
                <div className="text-base font-bold text-emerald-400">{batchResult.total_processed - batchResult.empty_filtered_count}</div>
              </div>
              <div className="p-2 rounded bg-[#0e1612] border border-emerald-950">
                <div className="text-[10px] text-slate-400 uppercase">Empty Filtered</div>
                <div className="text-base font-bold text-slate-300">{batchResult.empty_filtered_count}</div>
              </div>
              <div className="p-2 rounded bg-[#0e1612] border border-emerald-950">
                <div className="text-[10px] text-slate-400 uppercase">Species Count</div>
                <div className="text-base font-bold text-white">{Object.keys(speciesCounts).length}</div>
              </div>
            </div>

            {Object.keys(speciesCounts).length > 0 && (
              <div className="space-y-1 pt-1">
                <div className="text-[10px] font-bold uppercase text-slate-400">Species Breakdown (How Many):</div>
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(speciesCounts).map(([sp, count]) => (
                    <span key={sp} className="px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-800 text-emerald-300 text-[11px] font-mono">
                      {sp}: <b>{count}</b>
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="pt-2 flex justify-between items-center border-t border-emerald-950">
              <span className="text-[11px] text-emerald-400 font-mono">✓ Excel exported automatically</span>
              <button
                type="button"
                onClick={() => downloadExcel()}
                className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-black font-bold text-xs flex items-center gap-1 shadow-sm"
              >
                <span>📊 Re-download Excel (.xlsx)</span>
              </button>
            </div>
          </div>
        )}

        <div className="flex justify-end space-x-2 border-t border-emerald-950 pt-3">
          <button onClick={onClose} className="px-3 py-1.5 text-xs text-slate-400 hover:text-white">
            Close
          </button>
          <button
            onClick={handleUpload}
            disabled={loading || files.length === 0}
            className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-black font-bold text-xs"
          >
            {loading ? `Processing ${files.length} Photos...` : `Process ${files.length || ''} Photos & Export Excel`}
          </button>
        </div>
      </div>
    </div>
  );
}
