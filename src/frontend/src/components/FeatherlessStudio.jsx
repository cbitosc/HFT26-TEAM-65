import React, { useState } from 'react';

export default function FeatherlessStudio({ status }) {
  const [prompt, setPrompt] = useState('');
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);

  const generateReport = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/featherless/summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ custom_instructions: prompt })
      });
      const data = await res.json();
      setSummary(data);
    } catch (e) {
      alert('Error generating summary: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-[#121c17] border border-emerald-900/40 rounded-xl p-5 space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h3 className="font-bold text-base text-slate-100">
            Featherless AI — Ecological Synthesis & Narrative Studio
          </h3>
          <p className="text-xs text-slate-400">
            Synthesizes filtered telemetry into publication-ready executive findings and recommendations.
          </p>
        </div>
        <button
          onClick={generateReport}
          disabled={loading}
          className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-black font-bold text-xs shadow transition"
        >
          {loading ? 'Synthesizing...' : 'Generate Synthesis'}
        </button>
      </div>

      <div>
        <label className="block text-xs font-semibold text-slate-300 mb-1">
          Researcher Focus (Optional):
        </label>
        <input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="e.g. Focus on predator-prey timing overlap..."
          className="w-full bg-[#0e1612] border border-emerald-900/60 rounded-lg p-2.5 text-xs text-slate-200"
        />
      </div>

      <div className="border border-emerald-950/80 rounded-xl bg-[#0a0f0d] p-6 text-xs text-slate-300">
        {summary ? (
          <div className="space-y-4">
            <div className="flex justify-between items-center border-b border-emerald-950 pb-2 text-[10px] text-slate-400 font-mono">
              <span className="text-emerald-400 font-bold">{summary.provider}</span>
              <span>Generated at {new Date(summary.generated_at).toLocaleTimeString()}</span>
            </div>
            <pre className="whitespace-pre-wrap font-sans text-xs leading-relaxed text-slate-200">
              {summary.summary_markdown}
            </pre>
          </div>
        ) : (
          <p className="italic text-slate-500">
            Click "Generate Synthesis" to generate automated ecological report.
          </p>
        )}
      </div>
    </div>
  );
}
