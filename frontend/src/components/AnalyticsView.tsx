import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, CartesianGrid } from 'recharts';
import { TrendingUp, Activity, CheckCircle, AlertOctagon, BarChart3, AlertTriangle } from 'lucide-react';

/**
 * Analytics — every number on this page comes from MongoDB (via GET /api/analytics).
 * There is NO baseline/fallback dataset: when the API is unavailable or the
 * database is empty the UI states that explicitly instead of showing numbers.
 *
 * DESCRIPTIVE analytics only. This view performs no forecasting; predictive
 * analytics is not implemented (see the note rendered at the bottom).
 */
interface AnalyticsPayload {
  total_inspections: number;
  pass_count: number;
  rework_count: number;
  fail_count: number;
  review_required_count?: number;
  scored_inspection_count?: number;
  yield_rate: string | null;
  average_quality_score: number | string | null;
  defect_distribution: Record<string, number>;
  last_updated?: string;
}

export const AnalyticsView: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsPayload | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get('/api/analytics')
      .then(res => {
        setAnalytics(res.data);
        setLoadError(null);
      })
      .catch(err => {
        setAnalytics(null);
        setLoadError(err.response?.data?.error || err.message || 'Analytics API unavailable');
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-10 text-center text-slate-400">
        <Activity className="w-8 h-8 text-slate-600 mx-auto mb-3 animate-pulse" />
        <p className="text-sm font-semibold text-slate-300">Loading analytics from the database…</p>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="bg-rose-950/40 border border-rose-800/70 rounded-xl p-8 text-center space-y-2">
        <AlertTriangle className="w-10 h-10 text-rose-400 mx-auto" />
        <p className="text-sm font-bold text-rose-300">Analytics unavailable</p>
        <p className="text-xs text-rose-200/70 max-w-lg mx-auto">
          No data could be retrieved from the analytics API. No placeholder figures are shown.
        </p>
        <p className="text-[11px] text-rose-200/50 mono">{loadError}</p>
      </div>
    );
  }

  const hasData = analytics.total_inspections > 0;

  const defectBarData = Object.entries(analytics.defect_distribution || {}).map(([key, val]) => ({
    name: key.toUpperCase(),
    count: val
  }));

  const pieData = [
    { name: 'Pass (No Defect)', value: analytics.pass_count, color: '#10b981' },
    { name: 'Rework Required', value: analytics.rework_count, color: '#f59e0b' },
    { name: 'Review Required', value: analytics.review_required_count ?? 0, color: '#8b5cf6' },
    { name: 'Critical Reject', value: analytics.fail_count, color: '#ef4444' },
  ].filter(p => p.value > 0);

  return (
    <div className="space-y-6">
      {!hasData && (
        <div className="bg-amber-950/50 border border-amber-800 rounded-xl p-4 text-xs text-amber-200/90">
          <b>No inspections recorded in the database yet.</b> All counters below are real zeros. Run an inspection in the
          Inspection Studio and the database-backed analytics will populate.
        </div>
      )}

      {/* Top Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
            <span>TOTAL INSPECTIONS</span>
            <Activity className="w-4 h-4 text-blue-400" />
          </div>
          <p className="text-2xl font-black mono text-white mt-2">{analytics.total_inspections}</p>
          <span className="text-[11px] text-slate-400 font-medium">Recorded in MongoDB</span>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
            <span>FIRST-PASS YIELD</span>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-black mono text-emerald-400 mt-2">
            {analytics.yield_rate ?? '—'}
          </p>
          <span className="text-[11px] text-slate-400 font-medium">
            {analytics.yield_rate === null ? 'No scored inspections yet' : 'Pass + Rework over total inspections'}
          </span>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
            <span>AVERAGE AI QUALITY SCORE</span>
            <CheckCircle className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-2xl font-black mono text-cyan-400 mt-2">
            {analytics.average_quality_score ?? '—'}
          </p>
          <span className="text-[11px] text-slate-400 font-medium">
            Project-defined AI score · {analytics.scored_inspection_count ?? 0} scored inspection(s)
            {analytics.review_required_count ? ` · ${analytics.review_required_count} withheld (review required)` : ''}
          </span>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
            <span>CRITICAL REJECTS</span>
            <AlertOctagon className="w-4 h-4 text-rose-400" />
          </div>
          <p className="text-2xl font-black mono text-rose-400 mt-2">{analytics.fail_count}</p>
          <span className="text-[11px] text-slate-400 font-medium">Inspections scored FAIL</span>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Defect Distribution Bar Chart */}
        <div className="lg:col-span-7 bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
          <h4 className="text-sm font-bold text-slate-200 flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-blue-400" />
            Defect Frequency by Class (recorded inspections)
          </h4>
          <div className="h-64 w-full">
            {defectBarData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={defectBarData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }} 
                  />
                  <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">
                No defect records in the database yet.
              </div>
            )}
          </div>
        </div>

        {/* Quality Split Pie Chart */}
        <div className="lg:col-span-5 bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
          <h4 className="text-sm font-bold text-slate-200">Inspection Outcome Breakdown</h4>
          <div className="h-64 w-full flex items-center justify-center">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={85}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }} 
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-xs text-slate-500">No inspection records yet.</div>
            )}
          </div>
          {pieData.length > 0 && (
            <div className="flex flex-wrap justify-center gap-4 text-xs font-semibold">
              {pieData.map(p => (
                <span key={p.name} className="flex items-center gap-1.5" style={{ color: p.color }}>
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: p.color }}></span>
                  {p.name}: {p.value}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Scope note: descriptive vs predictive */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 text-[11px] text-slate-400 leading-relaxed">
        <b className="text-slate-300">Scope:</b> this dashboard is <b>descriptive only</b> — it summarizes records that already
        exist in the inspection database.
        <span className="block mt-1">
          <b className="text-amber-300">Prediction unavailable</b> — insufficient historical/validated model data to fit or
          validate a forecasting model, so no trend projection is shown.
        </span>
        {analytics.last_updated && (
          <span className="block mt-1 text-slate-500 mono">Last aggregated: {analytics.last_updated}</span>
        )}
      </div>
    </div>
  );
};
