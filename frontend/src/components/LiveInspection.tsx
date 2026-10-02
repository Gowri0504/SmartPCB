import React, { useState, useRef } from 'react';
import axios from 'axios';
import { 
  Upload, Eye, AlertTriangle, CheckCircle, ShieldAlert, 
  FileText, Table, Wrench, RefreshCw, Layers, Info, XOctagon
} from 'lucide-react';

/**
 * SmartPCB-XAI unified inspection contract v1.0 (mirrors ai/inference/engine.py).
 *
 * `quality_score` is NULLABLE by design: the engine withholds the score when
 * zero detections from both detectors are indistinguishable from a silent
 * detection failure (zero-detection safety rule, contract state (b)).
 * Every consumer of this interface must handle `quality_score === null`.
 */
export interface InspectionResult {
  contract_version?: string;
  inspection_status?: 'SUCCESS' | 'ERROR' | string;
  inspection_id: string;
  image_id?: string;
  timestamp: string;
  image_path?: string;
  preview_image_base64?: string | null;
  image_dimensions?: { width: number; height: number };
  quality_score: {
    overall_score: number | null;
    grade: string;
    status: string;
    defect_risk: string;
    component_integrity: number;
    defect_count: number;
    summary: string;
    formula?: string;
  } | null;
  components: Array<{
    id: string;
    class: string;
    confidence: number;
    bbox: number[];
  }>;
  defects: Array<{
    id: string;
    class: string;
    confidence: number;
    bbox: number[];
    near_component?: string;
    severity: {
      score: number;
      level: string;
      color: string;
      explanation: string;
    };
  }>;
  component_count?: number;
  defect_count?: number;
  severity?: Array<{
    defect_id: string;
    class: string;
    level: string | null;
    score: number | null;
    color: string | null;
  }>;
  recommendations: Array<{
    title: string;
    probable_causes: string[];
    inspection_steps: string[];
    repair_actions: string[];
    verification_steps: string[];
    ipc_standard: string;
    safety_notes?: string[];
  }>;
  pipeline_warnings?: string[];
  suspicious_zero_detection?: boolean;
  review_required?: boolean;
  models_available?: boolean | null;
  model_version?: { component?: string | null; defect?: string | null; engine_version?: string; inference_device?: string | null } | string | null;
  inference_time_ms?: number | null;
  xai?: {
    explained_defect_id?: string;
    explained_class?: string;
    attribution_method?: string;
    disclaimer?: string;
    interpretation?: string;
    overlay_base64?: string;
    error?: string;
  };
}

const getReviewState = (result: InspectionResult) => {
  if (result.inspection_status === 'ERROR') return 'ERROR';
  if (result.review_required || result.suspicious_zero_detection) return 'REVIEW_REQUIRED';
  return 'SUCCESS';
};

const formatModelVersion = (mv: InspectionResult['model_version']): string => {
  if (!mv) return 'not reported';
  if (typeof mv === 'string') return mv;
  const parts = [mv.component, mv.defect].filter(Boolean);
  if (parts.length === 0) return mv.engine_version || 'not reported';
  return `${parts.join(' + ')} (engine ${mv.engine_version ?? 'n/a'}, ${mv.inference_device ?? 'device n/a'})`;
};

interface LiveInspectionProps {
  onInspectionComplete?: (result: InspectionResult) => void;
}

export const LiveInspection: React.FC<LiveInspectionProps> = ({ onInspectionComplete }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<InspectionResult | null>(null);
  const [showComponents, setShowComponents] = useState(true);
  const [showDefects, setShowDefects] = useState(true);
  const [showXAI, setShowXAI] = useState(false);
  const [confThreshold, setConfThreshold] = useState(0.20);
  const [selectedItem, setSelectedItem] = useState<any | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const componentCount = result ? (result.component_count ?? result.components.length) : 0;
  const defectCount = result ? (result.defect_count ?? result.defects.length) : 0;
  const reviewState = result ? getReviewState(result) : null;
  const quality = result?.quality_score ?? null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResult(null);
      setSelectedItem(null);
    }
  };

  const handleLoadSample = async (samplePath: string, sampleName: string) => {
    try {
      const response = await fetch(samplePath);
      const blob = await response.blob();
      const file = new File([blob], sampleName, { type: 'image/jpeg' });
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(blob));
      setResult(null);
      setSelectedItem(null);
    } catch (err: any) {
      console.error("Failed to load sample image", err);
    }
  };

  const handleRunInspection = async () => {
    if (!selectedFile) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('image', selectedFile);
      formData.append('confidence_threshold', confThreshold.toString());

      const res = await axios.post('/api/inspection/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(res.data);
      onInspectionComplete?.(res.data);
    } catch (err: any) {
      console.error(err);
      alert('Inspection failed: ' + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = async () => {
    if (!result) return;
    try {
      const res = await axios.post('/api/reports/pdf', { inspection_data: result }, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${result.inspection_id}_report.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err: any) {
      alert('Failed to download PDF report: ' + err.message);
    }
  };

  const handleDownloadExcel = async () => {
    if (!result) return;
    try {
      const res = await axios.post('/api/reports/excel', { inspection_data: result }, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${result.inspection_id}_audit.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err: any) {
      alert('Failed to download Excel report: ' + err.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload & Control Header */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 backdrop-blur-sm shadow-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            accept="image/*" 
            className="hidden" 
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2.5 rounded-lg border border-slate-700 transition font-medium text-sm"
          >
            <Upload className="w-4 h-4 text-blue-400" />
            {selectedFile ? selectedFile.name : "Select PCB Image"}
          </button>

          {/* Quick Demo Boards Selector */}
          <select
            onChange={(e) => {
              if (e.target.value) {
                const val = e.target.value;
                const name = e.target.options[e.target.selectedIndex].text;
                handleLoadSample(val, name);
              }
            }}
            className="bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-2.5 rounded-lg border border-slate-700 text-sm font-medium cursor-pointer"
            defaultValue=""
          >
            <option value="" disabled>Load Real Demo Board...</option>
            <option value="/samples/sample_defect_board1.jpg">Defect Board 1 (DeepPCB - Shorts/Opens/Spurs)</option>
            <option value="/samples/sample_defect_board2.jpg">Defect Board 2 (DeepPCB - Pinholes/Spurious Copper)</option>
            <option value="/samples/sample_smt_board1.jpg">SMT Board 1 (FICS Industrial - Capacitors/Resistors)</option>
            <option value="/samples/sample_smt_board2.jpg">SMT Board 2 (FICS Industrial - Multi-Component)</option>
          </select>

          <div className="flex items-center gap-3 bg-slate-950 px-4 py-2 rounded-lg border border-slate-800 text-sm">
            <span className="text-slate-400 font-medium">Confidence:</span>
            <input 
              type="range" 
              min="0.1" 
              max="0.9" 
              step="0.05"
              value={confThreshold}
              onChange={(e) => setConfThreshold(parseFloat(e.target.value))}
              className="w-24 accent-blue-500 cursor-pointer"
            />
            <span className="mono text-blue-400 font-semibold">{Math.round(confThreshold * 100)}%</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRunInspection}
            disabled={!selectedFile || loading}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white px-5 py-2.5 rounded-lg font-semibold shadow-lg shadow-blue-600/30 transition"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Eye className="w-4 h-4" />}
            {loading ? "Analyzing Optical Patterns..." : "Run Inspection"}
          </button>

          {result && (
            <div className="flex items-center gap-2 border-l border-slate-800 pl-3">
              <button
                onClick={handleDownloadPDF}
                className="flex items-center gap-1.5 bg-rose-950/60 hover:bg-rose-900/80 text-rose-300 border border-rose-800/60 px-3 py-2 rounded-lg text-xs font-semibold transition"
              >
                <FileText className="w-3.5 h-3.5" /> PDF Report
              </button>
              <button
                onClick={handleDownloadExcel}
                className="flex items-center gap-1.5 bg-emerald-950/60 hover:bg-emerald-900/80 text-emerald-300 border border-emerald-800/60 px-3 py-2 rounded-lg text-xs font-semibold transition"
              >
                <Table className="w-3.5 h-3.5" /> Excel Audit
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Inspection status banner — three mutually exclusive states, never a silent PASS */}
      {result && reviewState === 'ERROR' && (
        <div className="bg-rose-950/70 border border-rose-700 rounded-xl p-4 flex items-start gap-3 shadow-xl">
          <XOctagon className="w-5 h-5 text-rose-400 mt-0.5 shrink-0" />
          <div className="text-sm">
            <p className="font-bold text-rose-300">Inspection FAILED (status: ERROR)</p>
            <p className="text-rose-200/80 text-xs mt-1">
              The inference pipeline did not produce a result. No quality score exists for this image — this is
              an execution failure, not a clean board.
            </p>
          </div>
        </div>
      )}

      {result && reviewState === 'REVIEW_REQUIRED' && (
        <div className="bg-amber-950/70 border border-amber-600 rounded-xl p-4 flex items-start gap-3 shadow-xl">
          <AlertTriangle className="w-5 h-5 text-amber-400 mt-0.5 shrink-0" />
          <div className="text-sm space-y-1.5">
            <p className="font-bold text-amber-300">REVIEW REQUIRED — zero detections, result not trusted</p>
            <p className="text-amber-200/80 text-xs">
              Both detectors returned zero results on a non-trivial image. A genuinely clean board and a silent
              detection failure (domain shift, class mismatch, preprocessing issue) are indistinguishable here.
              The quality score is deliberately withheld — do not read this as a perfect board.
            </p>
            {(result.pipeline_warnings?.length ?? 0) > 0 && (
              <ul className="text-[11px] text-amber-200/70 list-disc list-inside space-y-0.5">
                {result.pipeline_warnings!.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            )}
          </div>
        </div>
      )}

      {result && reviewState === 'SUCCESS' && quality && (
        <div className={`rounded-xl p-3.5 border flex items-start gap-3 shadow-xl text-xs ${
          quality.status === 'PASS'
            ? 'bg-emerald-950/60 border-emerald-800 text-emerald-300'
            : quality.status.includes('REWORK')
              ? 'bg-amber-950/60 border-amber-800 text-amber-300'
              : 'bg-rose-950/60 border-rose-800 text-rose-300'
        }`}>
          {quality.status === 'PASS' ? <CheckCircle className="w-4 h-4 mt-0.5 shrink-0" /> : <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />}
          <div>
            <span className="font-bold">Inspection complete — {quality.status}.</span>{' '}
            {componentCount > 0 && defectCount === 0
              ? `${componentCount} components detected and zero defects. This is a computed zero-defect result (components were found, so the pipeline is demonstrably executing).`
              : `${defectCount} defect(s) detected across ${componentCount} component(s).`}
          </div>
        </div>
      )}

      {/* Main Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Viewport / Interactive Canvas */}
        <div className="lg:col-span-8 bg-slate-900/80 border border-slate-800 rounded-xl p-5 flex flex-col items-center justify-center min-h-[520px] relative overflow-hidden shadow-xl">
          {/* Layer toggles */}
          {result && (
            <div className="absolute top-4 left-4 z-10 flex items-center gap-2 bg-slate-950/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-800 text-xs">
              <span className="text-slate-400 font-semibold flex items-center gap-1">
                <Layers className="w-3.5 h-3.5 text-blue-400" /> Overlays:
              </span>
              <button
                onClick={() => setShowComponents(!showComponents)}
                className={`px-2 py-1 rounded transition ${showComponents ? 'bg-blue-600/30 text-blue-300 border border-blue-500/50' : 'text-slate-500'}`}
              >
                Components ({componentCount})
              </button>
              <button
                onClick={() => setShowDefects(!showDefects)}
                className={`px-2 py-1 rounded transition ${showDefects ? 'bg-rose-600/30 text-rose-300 border border-rose-500/50' : 'text-slate-500'}`}
              >
                Defects ({defectCount})
              </button>
              <button
                onClick={() => setShowXAI(!showXAI)}
                className={`px-2 py-1 rounded transition ${showXAI ? 'bg-purple-600 text-white font-bold shadow-lg shadow-purple-600/30' : 'text-slate-400 hover:text-white'}`}
              >
                XAI Overlay {result.xai?.overlay_base64 ? '(Active)' : ''}
              </button>
            </div>
          )}

          {/* Active Mode Badge — label comes from the engine's real method name */}
          {result && showXAI && result.xai?.overlay_base64 && (
            <div className="absolute top-4 right-4 z-10 bg-purple-950/90 text-purple-300 border border-purple-800/80 px-3 py-1 rounded-full text-xs font-semibold backdrop-blur-md">
              {result.xai.attribution_method === 'activation_energy_approximation'
                ? 'Attribution: activation-energy approximation (not Grad-CAM++)'
                : `Attribution method: ${result.xai.attribution_method || 'not reported'}`}
            </div>
          )}

          {/* Image Display */}
          {result?.preview_image_base64 ? (
            <div className="relative max-h-[620px] w-full flex items-center justify-center overflow-auto rounded-lg border border-slate-800">
              <img 
                src={showXAI && result.xai?.overlay_base64 ? result.xai.overlay_base64 : result.preview_image_base64} 
                alt="Analyzed PCB Preview" 
                className="max-h-[600px] w-auto object-contain rounded shadow-2xl"
              />
            </div>
          ) : previewUrl ? (
            <div className="relative max-h-[620px] w-full flex items-center justify-center overflow-auto rounded-lg border border-slate-800">
              <img 
                src={previewUrl} 
                alt="Source PCB Board" 
                className="max-h-[600px] w-auto object-contain rounded shadow-2xl"
              />
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center text-slate-500 py-16">
              <div className="w-16 h-16 rounded-full bg-slate-800/80 flex items-center justify-center mb-4 text-slate-400">
                <Upload className="w-8 h-8" />
              </div>
              <p className="text-base font-semibold text-slate-300">No PCB Image Loaded</p>
              <p className="text-xs text-slate-500 max-w-sm text-center mt-1">
                Upload a high-resolution industrial PCB image or select a sample board to begin explainable optical analysis.
              </p>
            </div>
          )}
        </div>

        {/* Right: Inspection Telemetry & Results */}
        <div className="lg:col-span-4 space-y-5">
          {result ? (
            <>
              {/* Overall Quality Score Card */}
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">AI Inspection Score</p>
                    <div className="flex items-baseline gap-2 mt-1">
                      {quality && typeof quality.overall_score === 'number' ? (
                        <>
                          <span className="text-3xl font-extrabold mono text-white">{quality.overall_score}</span>
                          <span className="text-slate-500 font-semibold text-sm">/ 100</span>
                        </>
                      ) : (
                        <span className="text-xl font-extrabold mono text-amber-400">SCORE WITHHELD</span>
                      )}
                    </div>
                    <p className="text-[10px] text-slate-500 mt-1">AI-derived inspection score (project-defined formula — not an IPC numeric score)</p>
                  </div>
                  <div className={`px-3.5 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider border ${
                    !quality ? 'bg-amber-950 text-amber-400 border-amber-800' :
                    quality.status === 'PASS' ? 'bg-emerald-950 text-emerald-400 border-emerald-800' :
                    quality.status.includes('REWORK') ? 'bg-amber-950 text-amber-400 border-amber-800' :
                    'bg-rose-950 text-rose-400 border-rose-800'
                  }`}>
                    {quality ? quality.status : (reviewState === 'ERROR' ? 'ERROR' : 'REVIEW_REQUIRED')}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-800 text-xs">
                  <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                    <span className="text-slate-400">Defect Count:</span>
                    <p className="mono text-base font-bold text-rose-400">{defectCount}</p>
                  </div>
                  <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                    <span className="text-slate-400">Components:</span>
                    <p className="mono text-base font-bold text-blue-400">{componentCount}</p>
                  </div>
                </div>

                <p className="text-xs text-slate-400 bg-slate-950/60 p-3 rounded-lg border border-slate-800 leading-relaxed">
                  {quality?.summary
                    || (reviewState === 'ERROR'
                      ? 'No result was produced for this image. See pipeline warnings.'
                      : 'Quality score withheld: both detectors returned zero results, so a clean board cannot be distinguished from a detection failure.')}
                </p>

                <div className="text-[10px] text-slate-500 space-y-1 pt-1 border-t border-slate-800">
                  <p><b>Models:</b> <span className="mono break-all">{formatModelVersion(result.model_version)}</span></p>
                  <p><b>Inference time:</b> <span className="mono">{typeof result.inference_time_ms === 'number' ? `${result.inference_time_ms} ms` : 'not reported'}</span></p>
                  <p><b>Image ID:</b> <span className="mono break-all">{result.image_id || 'not reported'}</span></p>
                  <p><b>Contract:</b> <span className="mono">v{result.contract_version || '1.0'}</span> · <b>Status:</b> <span className="mono">{result.inspection_status || 'SUCCESS'}</span></p>
                </div>
              </div>

              {/* Pipeline Warnings (non-review-required cases) */}
              {reviewState !== 'REVIEW_REQUIRED' && (result.pipeline_warnings?.length ?? 0) > 0 && (
                <div className="bg-slate-900/90 border border-amber-800/60 rounded-xl p-4 shadow-xl space-y-2">
                  <h4 className="text-xs font-bold text-amber-300 flex items-center gap-2">
                    <Info className="w-3.5 h-3.5" /> Pipeline Warnings
                  </h4>
                  <ul className="text-[11px] text-slate-300 list-disc list-inside space-y-1">
                    {result.pipeline_warnings!.map((w, i) => <li key={i}>{w}</li>)}
                  </ul>
                </div>
              )}

              {/* Detected Defects List */}
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-rose-400" />
                    Detected Defects ({defectCount})
                  </h4>
                </div>

                <div className="max-h-60 overflow-y-auto space-y-2 pr-1">
                  {result.defects.length > 0 ? (
                    result.defects.map((d) => (
                      <div 
                        key={d.id}
                        onClick={() => setSelectedItem(d)}
                        className={`p-3 rounded-lg border cursor-pointer transition ${
                          selectedItem?.id === d.id ? 'bg-slate-800 border-rose-500' : 'bg-slate-950 border-slate-800 hover:border-slate-700'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-xs uppercase text-slate-200">{d.class}</span>
                          <span className="text-[10px] font-extrabold px-2 py-0.5 rounded" style={{ backgroundColor: `${d.severity.color}20`, color: d.severity.color }}>
                            {d.severity.level} ({d.severity.score})
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 mt-1 leading-snug">
                          Confidence: {Math.round(d.confidence * 100)}% | Near: {d.near_component || 'Ground / Signal Plane'}
                        </p>
                      </div>
                    ))
                  ) : reviewState === 'REVIEW_REQUIRED' ? (
                    <div className="text-center py-6 text-amber-400 text-xs font-semibold flex items-center justify-center gap-2">
                      <AlertTriangle className="w-4 h-4" /> No defects detected — but this result is NOT verified. See REVIEW REQUIRED notice above.
                    </div>
                  ) : reviewState === 'ERROR' ? (
                    <div className="text-center py-6 text-rose-400 text-xs font-semibold flex items-center justify-center gap-2">
                      <XOctagon className="w-4 h-4" /> Inspection failed — no detection data exists.
                    </div>
                  ) : (
                    <div className="text-center py-6 text-emerald-400 text-xs font-semibold flex items-center justify-center gap-2">
                      <CheckCircle className="w-4 h-4" /> Zero defects detected ({componentCount} components confirmed the pipeline executed).
                    </div>
                  )}
                </div>
              </div>

              {/* Suggested Engineering Action (rule-based knowledge engine) */}
              {(result.recommendations?.length ?? 0) > 0 && (
                <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-3">
                  <h4 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                    <Wrench className="w-4 h-4 text-amber-400" />
                    Suggested Engineering Action
                  </h4>
                  <p className="text-[10px] text-slate-500 -mt-1">
                    Rule-Based Root Cause Knowledge Engine — static expert-curated guidance, not machine-learned output.
                  </p>
                  <div className="max-h-56 overflow-y-auto space-y-3 pr-1 text-xs">
                    {result.recommendations.map((r, idx) => (
                      <div key={idx} className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-1.5">
                        <p className="font-bold text-amber-300">{r.title}</p>
                        <p className="text-slate-400"><b>Possible cause (not proven causality):</b> {r.probable_causes?.[0] ?? 'n/a'}</p>
                        <p className="text-emerald-300"><b>Suggested action:</b> {r.repair_actions?.[0] ?? 'n/a'}</p>
                        {(r.safety_notes?.length ?? 0) > 0 && (
                          <details className="text-[10px] text-amber-200/80">
                            <summary className="cursor-pointer font-semibold">Safety precautions ({r.safety_notes!.length})</summary>
                            <ul className="list-disc list-inside mt-1 space-y-0.5">
                              {r.safety_notes!.map((s, si) => <li key={si}>{s}</li>)}
                            </ul>
                          </details>
                        )}
                        <p className="text-[10px] text-slate-500">Reference guidance: {r.ipc_standard}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* XAI panel */}
              {result.xai && Object.keys(result.xai).length > 0 && (
                <div className="bg-slate-900/90 border border-purple-900/50 rounded-xl p-5 shadow-xl space-y-2">
                  <h4 className="text-sm font-bold text-slate-200">Explainability (XAI)</h4>
                  <p className="text-[11px] text-slate-400">
                    <b>Method:</b> <span className="mono">{result.xai.attribution_method || 'not reported'}</span>
                  </p>
                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    {result.xai.error || result.xai.interpretation || 'No attribution produced for this image (XAI runs only when at least one defect is detected).'}
                  </p>
                  {result.xai.disclaimer && (
                    <p className="text-[10px] text-slate-500 bg-slate-950/60 p-2 rounded border border-slate-800 leading-relaxed">
                      {result.xai.disclaimer}
                    </p>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-6 text-center space-y-3 text-slate-400">
              <ShieldAlert className="w-10 h-10 text-slate-600 mx-auto" />
              <p className="text-sm font-semibold text-slate-300">Awaiting PCB Scan</p>
              <p className="text-xs text-slate-500">
                Load an image and click <b>Run Inspection</b> to calculate quality telemetry, defect severities, and XAI feature attributions.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
