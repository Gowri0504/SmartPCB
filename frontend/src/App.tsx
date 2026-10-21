import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Cpu, Eye, Layers, BarChart3, MessageSquarePlus,
  Award, Shield, Sun, Moon
} from 'lucide-react';
import { LiveInspection, InspectionResult } from './components/LiveInspection';
import { DigitalTwin } from './components/DigitalTwin';
import { AnalyticsView } from './components/AnalyticsView';
import { FeedbackView } from './components/FeedbackView';
import { ModelPerformance } from './components/ModelPerformance';

type TabType = 'INSPECTION' | 'DIGITAL_TWIN' | 'ANALYTICS' | 'FEEDBACK' | 'BENCHMARKS';

interface SystemStatus {
  express: { reachable: boolean; port: number };
  mongodb: { state: string; connected: boolean };
  ai_engine: { reachable: boolean; detail: any };
  checked_at: string;
}

export default function App() {
  const [activeTab, setActiveTab] = useState<TabType>('INSPECTION');
  const [lastInspection, setLastInspection] = useState<InspectionResult | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    try {
      const saved = localStorage.getItem('smartpcb-theme');
      if (saved === 'light' || saved === 'dark') return saved;
    } catch { /* storage unavailable */ }
    return 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem('smartpcb-theme', theme); } catch { /* ignore */ }
  }, [theme]);

  const toggleTheme = () => setTheme(t => (t === 'dark' ? 'light' : 'dark'));

  useEffect(() => {
    let cancelled = false;
    const probe = () => {
      axios.get('/api/system-status', { timeout: 6000 })
        .then(res => { if (!cancelled) { setSystemStatus(res.data); setStatusError(null); } })
        .catch(err => { if (!cancelled) { setSystemStatus(null); setStatusError(err.message); } });
    };
    probe();
    const timer = setInterval(probe, 30000);
    return () => { cancelled = true; clearInterval(timer); };
  }, []);

  const engineOnline = systemStatus?.ai_engine?.reachable === true;
  const engineLabel = systemStatus
    ? (engineOnline ? 'ENGINE ONLINE' : 'ENGINE UNREACHABLE')
    : (statusError ? 'STATUS UNKNOWN' : 'CHECKING…');
  const engineClass = engineOnline
    ? 'status-chip status-chip--online is-live'
    : systemStatus
      ? 'status-chip status-chip--offline'
      : 'status-chip status-chip--unknown';

  return (
    <div className="min-h-screen flex flex-col font-ui">
      {/* Top Industrial Header */}
      <header className="hmi-header">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3 min-w-0">
            <div className="brand-mark">
              <Cpu className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="brand-title">SmartPCB Inspection Studio</span>
                <span className="brand-tag">
                  Industry 4.0
                </span>
              </div>
              <p className="brand-sub">Automated Optical Inspection &amp; Manufacturing Analytics</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="nav-tablist hidden md:flex" role="tablist" aria-label="Primary">
            <button
              role="tab"
              aria-selected={activeTab === 'INSPECTION'}
              onClick={() => setActiveTab('INSPECTION')}
              className={`nav-tab ${activeTab === 'INSPECTION' ? 'is-active' : ''}`}
            >
              <Eye width={15} height={15} />
              Inspection
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'DIGITAL_TWIN'}
              onClick={() => setActiveTab('DIGITAL_TWIN')}
              className={`nav-tab ${activeTab === 'DIGITAL_TWIN' ? 'is-active' : ''}`}
            >
              <Layers width={15} height={15} />
              Board Map
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'ANALYTICS'}
              onClick={() => setActiveTab('ANALYTICS')}
              className={`nav-tab ${activeTab === 'ANALYTICS' ? 'is-active' : ''}`}
            >
              <BarChart3 width={15} height={15} />
              Analytics
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'FEEDBACK'}
              onClick={() => setActiveTab('FEEDBACK')}
              className={`nav-tab ${activeTab === 'FEEDBACK' ? 'is-active' : ''}`}
            >
              <MessageSquarePlus width={15} height={15} />
              Corrections
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'BENCHMARKS'}
              onClick={() => setActiveTab('BENCHMARKS')}
              className={`nav-tab ${activeTab === 'BENCHMARKS' ? 'is-active' : ''}`}
            >
              <Award width={15} height={15} />
              Benchmarks
            </button>
          </nav>

          {/* Mobile tab selector */}
          <select
            className="md:hidden select"
            style={{ width: 'auto', maxWidth: 240 }}
            value={activeTab}
            onChange={(e) => setActiveTab(e.target.value as TabType)}
          >
            <option value="INSPECTION">Inspection</option>
            <option value="DIGITAL_TWIN">Board Map</option>
            <option value="ANALYTICS">Analytics</option>
            <option value="FEEDBACK">Corrections</option>
            <option value="BENCHMARKS">Benchmarks</option>
          </select>

          {/* System Status + Theme Toggle */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={toggleTheme}
              className="theme-toggle"
              aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
              title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {theme === 'dark' ? <Sun width={18} height={18} /> : <Moon width={18} height={18} />}
            </button>
            <div
              title={systemStatus
                ? `Engine probe at ${systemStatus.checked_at}${engineOnline ? '' : ` — ${JSON.stringify(systemStatus.ai_engine?.detail)}`}`
                : (statusError || 'Probing backend…')}
              className={engineClass}
            >
              {engineLabel}
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 w-full max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'INSPECTION' && <LiveInspection onInspectionComplete={setLastInspection} />}
        {activeTab === 'DIGITAL_TWIN' && (
          <DigitalTwin
            inspectionData={lastInspection}
            onNavigateToInspection={() => setActiveTab('INSPECTION')}
          />
        )}
        {activeTab === 'ANALYTICS' && <AnalyticsView />}
        {activeTab === 'FEEDBACK' && <FeedbackView />}
        {activeTab === 'BENCHMARKS' && <ModelPerformance />}
      </main>

      {/* Footer */}
      <footer className="hmi-footer py-4 mt-4">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-blue-500" />
            <span>SmartPCB Inspection Studio &copy; 2026. Automated Optical Inspection for SMT Manufacturing.</span>
          </div>
          <div className="flex flex-wrap items-center gap-4 mono text-[11px]">
            <span>
              Engine:&nbsp;
              <b className={engineOnline ? 'text-emerald-400' : systemStatus ? 'text-rose-400' : 'text-slate-400'}>
                {systemStatus ? (engineOnline ? 'REACHABLE' : 'UNREACHABLE') : 'UNKNOWN'}
              </b>
            </span>
            <span>
              Database:&nbsp;
              <b className={systemStatus?.mongodb?.connected ? 'text-emerald-400' : systemStatus ? 'text-rose-400' : 'text-slate-400'}>
                {systemStatus?.mongodb?.state?.toUpperCase() || 'UNKNOWN'}
              </b>
            </span>
            {lastInspection?.model_version && typeof lastInspection.model_version === 'object' && (
              <span>
                Last run:&nbsp;
                <b className="text-blue-400">{(lastInspection.model_version as any).inference_device || 'not reported'}</b>
              </span>
            )}
          </div>
        </div>
      </footer>
    </div>
  );
}
