import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Award, Layers, ShieldCheck, Microscope, Cpu, CheckCircle2, AlertTriangle, FileWarning } from 'lucide-react';

interface Artifact {
  available: boolean;
  path?: string;
  size_bytes?: number;
  modified_at?: string;
  reason?: string;
  data?: any;
}

interface EvalResponse {
  generated_at: string;
  artifacts: Record<string, Artifact>;
}

const fmtMs = (v: any) => (typeof v === 'number' ? `${v.toFixed(2)} ms` : 'not reported');
const fmtNum = (v: any, digits = 4) => (typeof v === 'number' ? v.toFixed(digits) : 'not reported');

export const ModelPerformance: React.FC = () => {
  const [payload, setPayload] = useState<EvalResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get('/api/model-evaluation')
      .then(res => { setPayload(res.data); setError(null); })
      .catch(err => setError(err.response?.data?.error || err.message))
      .finally(() => setLoading(false));
  }, []);

  const artifacts = payload?.artifacts || {};
  const benchmark = artifacts.inference_benchmark;
  const bench = benchmark?.available ? benchmark.data : null;
  const componentMetrics = artifacts.component_metrics;
  const defectMetrics = artifacts.defect_metrics;

  const renderUnavailable = (a: Artifact | undefined, what: string) => (
    <div className="bg-slate-950 border border-amber-900/60 rounded-lg p-4 flex items-start gap-3 text-xs">
      <FileWarning className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
      <div>
        <p className="font-bold text-amber-300">NOT VERIFIED — no evaluation artifact has been generated</p>
        <p className="text-slate-400 mt-1">
          {a?.reason || `The ${what} report has not been produced on this machine. Run the evaluation script to generate it; until then no numbers are shown.`}
        </p>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Award className="w-5 h-5 text-amber-400" />
            Measured Evaluation Artifacts (read from disk)
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Every figure on this page is read verbatim from an evaluation artifact produced by a script in{' '}
            <span className="mono">scripts/evaluation/</span>. Nothing is hardcoded in the UI. Absent artifacts are
            reported as NOT VERIFIED rather than substituted with placeholder values.
          </p>
        </div>
        <span className={`text-xs font-bold px-3 py-1 rounded-full uppercase border ${
          payload ? 'text-emerald-400 bg-emerald-950 border-emerald-800/80' : 'text-rose-400 bg-rose-950 border-rose-800/80'
        }`}>
          {loading ? 'Loading…' : payload ? `Artifacts listed ${new Date(payload.generated_at).toLocaleTimeString()}` : 'Artifact endpoint unreachable'}
        </span>
      </div>

      {error && (
        <div className="bg-rose-950/60 border border-rose-800 rounded-xl p-4 text-xs text-rose-300">
          Could not read evaluation artifacts: {error}. No placeholder figures are shown.
        </div>
      )}

      {/* Hardware / environment benchmark */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-3">
        <h4 className="text-sm font-bold text-slate-200 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-blue-400" />
          Inference Benchmark — measured on this machine
        </h4>

        {!benchmark?.available ? (
          renderUnavailable(benchmark, 'inference benchmark')
        ) : (
          <>
            <div className="flex flex-wrap gap-2 text-[11px] mono">
              <span className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-300">device: {bench?.device?.type || 'not reported'}</span>
              <span className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-300">torch: {bench?.environment?.torch || bench?.torch_version || 'not reported'}</span>
              <span className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-300">cuda available: {String(bench?.environment?.cuda_available ?? bench?.cuda_available ?? 'not reported')}</span>
              <span className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-300">iterations: {bench?.iterations ?? 'not reported'}</span>
              <span className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-300">warmup discarded: {bench?.warmup_discarded ?? 'not reported'}</span>
              <span className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-500">artifact: {benchmark.path} ({new Date(benchmark.modified_at!).toLocaleString()})</span>
            </div>

            {bench?.timing_mean_ms && (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="bg-slate-950 text-slate-400 border-b border-slate-800">
                      <th className="p-2.5">Pipeline Stage</th>
                      <th className="p-2.5">Mean</th>
                      <th className="p-2.5">Median</th>
                      <th className="p-2.5">Min</th>
                      <th className="p-2.5">Max</th>
                      <th className="p-2.5">p95</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {Object.entries(bench.timing_mean_ms).map(([stage, mean]) => (
                      <tr key={stage} className={stage === 'total' ? 'bg-blue-950/20 font-bold text-blue-300' : 'text-slate-300'}>
                        <td className="p-2.5 mono">{stage}</td>
                        <td className="p-2.5 mono">{fmtMs(mean)}</td>
                        <td className="p-2.5 mono text-slate-400">{fmtMs(bench.timing_median_ms?.[stage])}</td>
                        <td className="p-2.5 mono text-slate-400">{fmtMs(bench.timing_min_ms?.[stage])}</td>
                        <td className="p-2.5 mono text-slate-400">{fmtMs(bench.timing_max_ms?.[stage])}</td>
                        <td className="p-2.5 mono text-slate-400">{fmtMs(bench.timing_p95_ms?.[stage])}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {bench?.scientific_honesty_note && (
              <p className="text-[11px] text-slate-500 bg-slate-950/60 border border-slate-800 rounded-lg p-3 leading-relaxed">
                {bench.scientific_honesty_note}
              </p>
            )}
          </>
        )}
      </div>

      {/* Per-class metrics — rendered ONLY from real artifacts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-3">
          <h4 className="text-sm font-bold text-slate-200 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-400" />
            Component Detection — per-class metrics
          </h4>
          {!componentMetrics?.available ? (
            renderUnavailable(componentMetrics, 'component model evaluation')
          ) : (
            <>
              <pre className="text-[10px] mono text-slate-300 bg-slate-950 border border-slate-800 rounded-lg p-3 max-h-72 overflow-auto">
                {JSON.stringify(componentMetrics.data, null, 2)}
              </pre>
              <p className="text-[10px] text-slate-500">Source: {componentMetrics.path}</p>
            </>
          )}
        </div>

        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-3">
          <h4 className="text-sm font-bold text-slate-200 flex items-center gap-2">
            <Microscope className="w-4 h-4 text-rose-400" />
            Defect Detection — per-class metrics
          </h4>
          {!defectMetrics?.available ? (
            renderUnavailable(defectMetrics, 'defect model evaluation')
          ) : (
            <>
              <pre className="text-[10px] mono text-slate-300 bg-slate-950 border border-slate-800 rounded-lg p-3 max-h-72 overflow-auto">
                {JSON.stringify(defectMetrics.data, null, 2)}
              </pre>
              <p className="text-[10px] text-slate-500">Source: {defectMetrics.path}</p>
            </>
          )}
        </div>
      </div>

      {/* Full pipeline run summary */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-3">
        <h4 className="text-sm font-bold text-slate-200 flex items-center gap-2">
          <Layers className="w-4 h-4 text-blue-400" />
          Full Pipeline Runs (image-level records)
        </h4>
        {!artifacts.full_pipeline_metrics?.available ? (
          renderUnavailable(artifacts.full_pipeline_metrics, 'pipeline metrics')
        ) : (
          <PipelineSummary artifact={artifacts.full_pipeline_metrics} />
        )}
      </div>

      {/* Scope + provenance note */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-xl space-y-2 text-xs text-slate-400">
        <h4 className="text-sm font-bold text-slate-200 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          Scope of these measurements
        </h4>
        <p>
          These artifacts record what the deployed checkpoints actually did on this machine and on the images listed in
          each file. They are <b>not</b> a held-out benchmark claim against a public leaderboard, and no mAP improvement
          over a baseline is asserted here unless a baseline evaluation artifact exists on disk.
        </p>
        <p>
          Where an artifact is missing, the correct statement is <b>NOT VERIFIED</b> — not a fabricated number. Per-class
          precision/recall requires ground-truth annotations for the evaluated images; without them, the pipeline
          artifacts above are a qualitative external generalization evaluation only.
        </p>
      </div>
    </div>
  );
};

const PipelineSummary: React.FC<{ artifact: Artifact }> = ({ artifact }) => {
  const records: any[] = Array.isArray(artifact.data) ? artifact.data : (artifact.data?.records || []);
  if (records.length === 0) {
    return (
      <div className="bg-slate-950 border border-amber-900/60 rounded-lg p-4 text-xs text-amber-300 flex items-center gap-2">
        <AlertTriangle className="w-4 h-4" />
        Artifact exists at {artifact.path} but contains no readable records.
      </div>
    );
  }
  const latencies = records.map(r => r.pipeline_latency_ms).filter((v: any) => typeof v === 'number');
  const totalComponents = records.reduce((a, r) => a + (r.components_detected || 0), 0);
  const totalDefects = records.reduce((a, r) => a + (r.defects_detected || 0), 0);
  const statuses: Record<string, number> = records.reduce((acc: Record<string, number>, r) => {
    const s = r.status || 'UNKNOWN';
    acc[s] = (acc[s] || 0) + 1;
    return acc;
  }, {});
  const sorted = [...latencies].sort((a, b) => a - b);
  const p95 = sorted.length ? sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * 0.95))] : null;
  const mean = latencies.length ? latencies.reduce((a, b) => a + b, 0) / latencies.length : null;

  return (
    <>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div className="bg-slate-950 border border-slate-800 rounded-lg p-3">
          <p className="text-slate-400">Images evaluated</p>
          <p className="mono text-lg font-bold text-white">{records.length}</p>
        </div>
        <div className="bg-slate-950 border border-slate-800 rounded-lg p-3">
          <p className="text-slate-400">Components detected (sum)</p>
          <p className="mono text-lg font-bold text-blue-400">{totalComponents}</p>
        </div>
        <div className="bg-slate-950 border border-slate-800 rounded-lg p-3">
          <p className="text-slate-400">Defects detected (sum)</p>
          <p className="mono text-lg font-bold text-rose-400">{totalDefects}</p>
        </div>
        <div className="bg-slate-950 border border-slate-800 rounded-lg p-3">
          <p className="text-slate-400">Pipeline latency (mean / p95)</p>
          <p className="mono text-sm font-bold text-amber-400">{fmtMs(mean)} / {fmtMs(p95)}</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 text-[11px]">
        {Object.entries(statuses).map(([s, n]) => (
          <span key={s} className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-300 mono">
            {s}: {n}
          </span>
        ))}
      </div>

      <div className="overflow-x-auto max-h-80 overflow-y-auto">
        <table className="w-full text-left text-xs">
          <thead className="sticky top-0">
            <tr className="bg-slate-950 text-slate-400 border-b border-slate-800">
              <th className="p-2.5">Image</th>
              <th className="p-2.5">Size</th>
              <th className="p-2.5">Comps</th>
              <th className="p-2.5">Defects</th>
              <th className="p-2.5">Avg comp conf</th>
              <th className="p-2.5">Avg defect conf</th>
              <th className="p-2.5">Score</th>
              <th className="p-2.5">Status</th>
              <th className="p-2.5">Latency</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {records.map((r, i) => (
              <tr key={i} className="text-slate-300">
                <td className="p-2.5 mono text-[11px] text-slate-400">{r.image}</td>
                <td className="p-2.5 mono text-[11px]">{r.width}×{r.height}</td>
                <td className="p-2.5 mono">{r.components_detected}</td>
                <td className="p-2.5 mono text-rose-400 font-semibold">{r.defects_detected}</td>
                <td className="p-2.5 mono text-slate-400">{fmtNum(r.avg_component_conf, 3)}</td>
                <td className="p-2.5 mono text-slate-400">{fmtNum(r.avg_defect_conf, 3)}</td>
                <td className="p-2.5 mono">{r.quality_score ?? 'null'}</td>
                <td className="p-2.5">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                    r.status === 'PASS' ? 'bg-emerald-950 text-emerald-400' :
                    r.status === 'REVIEW_REQUIRED' ? 'bg-amber-950 text-amber-400' : 'bg-rose-950 text-rose-400'
                  }`}>{r.status}</span>
                </td>
                <td className="p-2.5 mono text-slate-400">{fmtMs(r.pipeline_latency_ms)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-[10px] text-slate-500">
        Source: {artifact.path} ({artifact.size_bytes} bytes, modified {new Date(artifact.modified_at!).toLocaleString()})
        {' '}<CheckCircle2 className="w-3 h-3 inline text-emerald-500" /> read verbatim, unmodified.
      </p>
    </>
  );
};
