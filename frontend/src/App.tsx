import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Cpu, Eye, Layers, BarChart3, MessageSquarePlus, 
  Award, Shield 
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
    ? (engineOnline ? 'AI ENGINE ONLINE' : 'AI ENGINE UNREACHABLE')
    : (statusError ? 'STATUS UNKNOWN' : 'CHECKING…');

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-blue-600 selection:text-white">
      {/* Top Industrial Header */}
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-600/30 text-white font-extrabold">
              <Cpu className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-base tracking-tight text-white">SmartPCB-XAI</span>
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800/60 font-bold">
                  Industry 4.0
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">Explainable AI PCB Inspection & Manufacturing Analytics</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="hidden md:flex items-center gap-1 bg-slate-900/80 p-1 rounded-xl border border-slate-800 text-xs font-semibold">
            <button
              onClick={() => setActiveTab('INSPECTION')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg transition ${
                activeTab === 'INSPECTION' ? 'bg-blue-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              Inspection Studio
            </button>
            <button
              onClick={() => setActiveTab('DIGITAL_TWIN')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg transition ${
                activeTab === 'DIGITAL_TWIN' ? 'bg-blue-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              Digital Twin
            </button>
            <button
              onClick={() => setActiveTab('ANALYTICS')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg transition ${
                activeTab === 'ANALYTICS' ? 'bg-blue-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              Analytics
            </button>
            <button
              onClick={() => setActiveTab('FEEDBACK')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg transition ${
                activeTab === 'FEEDBACK' ? 'bg-blue-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <MessageSquarePlus className="w-3.5 h-3.5" />
              Corrections Pipeline
            </button>
            <button
              onClick={() => setActiveTab('BENCHMARKS')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg transition ${
                activeTab === 'BENCHMARKS' ? 'bg-blue-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Award className="w-3.5 h-3.5" />
              Research & Benchmarks
            </button>
          </nav>

          {/* System Status Indicator — live probe of /api/system-status, never assumed */}
          <div className="flex items-center gap-3 text-xs">
            <div
              title={systemStatus
                ? `AI engine probe at ${systemStatus.checked_at}${engineOnline ? '' : ` — ${JSON.stringify(systemStatus.ai_engine.detail)}`}`
                : (statusError || 'Probing backend…')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-full font-mono text-[11px] border ${
                engineOnline
                  ? 'bg-emerald-950/60 border-emerald-800/60 text-emerald-400'
                  : systemStatus
                    ? 'bg-rose-950/60 border-rose-800/60 text-rose-400'
                    : 'bg-slate-900 border-slate-700 text-slate-400'
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${engineOnline ? 'bg-emerald-400 animate-pulse' : systemStatus ? 'bg-rose-400' : 'bg-slate-500'}`}></span>
              {engineLabel}
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
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
      <footer className="border-t border-slate-800/80 bg-slate-950 py-4 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-blue-500" />
            <span>SmartPCB-XAI &copy; 2026. Explainable Optical Inspection Platform for SMT Manufacturing.</span>
          </div>
          <div className="flex items-center gap-4 text-[11px] mono">
            <span>
              AI Engine:{' '}
              <b className={engineOnline ? 'text-emerald-400' : systemStatus ? 'text-rose-400' : 'text-slate-400'}>
                {systemStatus ? (engineOnline ? 'REACHABLE' : 'UNREACHABLE') : 'UNKNOWN'}
              </b>
            </span>
            <span>
              MongoDB:{' '}
              <b className={systemStatus?.mongodb?.connected ? 'text-emerald-400' : systemStatus ? 'text-rose-400' : 'text-slate-400'}>
                {systemStatus?.mongodb?.state?.toUpperCase() || 'UNKNOWN'}
              </b>
            </span>
            {lastInspection?.model_version && typeof lastInspection.model_version === 'object' && (
              <span>
                Last inference device:{' '}
                <b className="text-blue-400">{lastInspection.model_version.inference_device || 'not reported'}</b>
              </span>
            )}
          </div>
        </div>
      </footer>
    </div>
  );
}
