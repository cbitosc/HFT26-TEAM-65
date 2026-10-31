import React, { useState, useEffect } from 'react';
import KPICards from './components/KPICards';
import DielActivityChart from './components/DielActivityChart';
import GalleryGrid from './components/GalleryGrid';
import SpatialMap from './components/SpatialMap';
import FeatherlessStudio from './components/FeatherlessStudio';
import UploadModal from './components/UploadModal';

export default function App() {
  const [activeTab, setActiveTab] = useState('analytics');
  const [metrics, setMetrics] = useState(null);
  const [temporal, setTemporal] = useState(null);
  const [spatial, setSpatial] = useState(null);
  const [featherlessStatus, setFeatherlessStatus] = useState(null);
  const [showUploadModal, setShowUploadModal] = useState(false);

  const reloadData = async () => {
    try {
      const [mRes, tRes, sRes, fRes] = await Promise.all([
        fetch('/api/analytics/overview').then(r => r.json()),
        fetch('/api/analytics/temporal').then(r => r.json()),
        fetch('/api/analytics/spatial').then(r => r.json()),
        fetch('/api/featherless/status').then(r => r.json())
      ]);
      setMetrics(mRes);
      setTemporal(tRes);
      setSpatial(sRes);
      setFeatherlessStatus(fRes);
    } catch (e) {
      console.error('Failed to load telemetry data:', e);
    }
  };

  useEffect(() => {
    reloadData();
  }, []);

  return (
    <div className="min-h-screen bg-[#0b100d] text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="border-b border-emerald-950/80 bg-[#0e1612]/90 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center text-black font-bold shadow-lg shadow-emerald-900/30">
              🐾
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-200 bg-clip-text text-transparent">
                  WildlifeAI Studio
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  React 18 &bull; CCT
                </span>
              </div>
              <p className="text-xs text-slate-400">Team 65: The Chosen One &bull; CBIT Hacktoberfest '26</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowUploadModal(true)}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-black shadow transition"
            >
              <span>+ Upload Frame</span>
            </button>
            <a
              href="/docs"
              target="_blank"
              rel="noreferrer"
              className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition"
            >
              Swagger Docs
            </a>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* KPI Cards */}
        <KPICards metrics={metrics} />

        {/* Tab Navigation */}
        <div className="flex items-center space-x-1 border-b border-emerald-950/60 pb-1 text-sm font-medium">
          {[
            { id: 'analytics', label: 'Diel & Analytics' },
            { id: 'gallery', label: 'Camera Trap Gallery' },
            { id: 'spatial', label: 'Spatial Stations' },
            { id: 'featherless', label: 'Featherless Insights' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-lg transition ${
                activeTab === tab.id
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Views */}
        {activeTab === 'analytics' && <DielActivityChart temporal={temporal} metrics={metrics} />}
        {activeTab === 'gallery' && <GalleryGrid onRefresh={reloadData} />}
        {activeTab === 'spatial' && <SpatialMap spatial={spatial} />}
        {activeTab === 'featherless' && <FeatherlessStudio status={featherlessStatus} />}
      </main>

      {/* Upload Modal */}
      {showUploadModal && (
        <UploadModal
          onClose={() => setShowUploadModal(false)}
          onSuccess={() => {
            setShowUploadModal(false);
            reloadData();
          }}
        />
      )}
    </div>
  );
}
