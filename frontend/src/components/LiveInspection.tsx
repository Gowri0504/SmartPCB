import React, { useState, useRef } from 'react';
import axios from 'axios';
import {
  Upload, Eye, AlertTriangle, CheckCircle, ShieldAlert,
  FileText, Table, Wrench, RefreshCw, Layers, Info, XOctagon,
  Clock, ScanLine, Target, Gauge, Zap, Download, FileDown
} from 'lucide-react';

/**
 * SmartPCB Inspection Studio — unified inspection contract v1.0
 * (mirrors ai/inference/engine.py).
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

const fmtTime = (ms: number | null | undefined) => {
  if (typeof ms !== 'number') return '—';
  if (ms >= 1000) return `${(ms / 1000).toFixed(2)} s`;
  return `${Math.round(ms)} ms`;
};

const fmtDate = (iso: string | undefined) => {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    if (isNaN(d.getTime())) return iso;
    const pad = (n: number) => n.toString().padStart(2, '0');
    return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}  ${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  } catch {
    return iso;
  }
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
  const [showAttribution, setShowAttribution] = useState(false);
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
      setShowAttribution(false);
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
      setShowAttribution(false);
    } catch (err: any) {
      console.error('Failed to load sample image', err);
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

  const statusKpiTone = (q: typeof quality) => {
    if (!q) return 'warning';
    if (q.status === 'PASS') return 'success';
    if (q.status.includes('REWORK')) return 'warning';
    return 'danger';
  };

  const attributionBadge = result?.xai?.attribution_method === 'activation_energy_approximation'
    ? 'Activation-energy approximation'
    : `Attribution: ${result?.xai?.attribution_method || 'n/a'}`;

  const viewerImgSrc =
    result?.preview_image_base64
      ? (showAttribution && result.xai?.overlay_base64 ? result.xai.overlay_base64 : result.preview_image_base64)
      : previewUrl
        ? previewUrl
        : null;

  const viewerImgAlt =
    result ? 'Inspection Result Overlay' : previewUrl ? 'Source PCB Image' : '';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Control Bar */}
      <div className="panel">
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 14, padding: '14px 16px' }}>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="image/*"
            style={{ display: 'none' }}
          />
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 10 }}>
            <button className="btn btn-sm" onClick={() => fileInputRef.current?.click()}>
              <Upload width={15} height={15} />
              {selectedFile ? selectedFile.name : 'Select PCB Image'}
            </button>

            <select
              className="select btn-sm"
              style={{ width: 'auto', minWidth: 260 }}
              onChange={(e) => {
                if (e.target.value) {
                  const name = e.target.options[e.target.selectedIndex].text;
                  handleLoadSample(e.target.value, name);
                  e.target.value = '';
                }
              }}
              defaultValue=""
            >
              <option value="" disabled>Load Demo Board…</option>
              <option value="/samples/sample_defect_board1.jpg">Defect Board 1 — Shorts / Opens / Spurs</option>
              <option value="/samples/sample_defect_board2.jpg">Defect Board 2 — Pinholes / Spurious Copper</option>
              <option value="/samples/sample_smt_board1.jpg">SMT Board 1 — Capacitors / Resistors</option>
              <option value="/samples/sample_smt_board2.jpg">SMT Board 2 — Multi-component</option>
            </select>

            <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '7px 12px', border: '1px solid #1e293b', borderRadius: 6, background: '#050b18' }}>
              <label htmlFor="conf" style={{ fontSize: 12, color: '#94a3b8', fontWeight: 600, whiteSpace: 'nowrap' }}>Confidence</label>
              <input
                id="conf"
                type="range"
                min={0.1} max={0.9} step={0.05}
                value={confThreshold}
                onChange={(e) => setConfThreshold(parseFloat(e.target.value))}
                className="input"
                style={{ width: 140 }}
              />
              <span className="mono" style={{ color: '#60a5fa', fontWeight: 700, minWidth: 40, textAlign: 'right' }}>
                {Math.round(confThreshold * 100)}%
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <button
              className="btn btn--primary btn-sm"
              onClick={handleRunInspection}
              disabled={!selectedFile || loading}
            >
              {loading ? <RefreshCw width={15} height={15} style={{ animation: 'spin 1s linear infinite' }} /> : <Eye width={15} height={15} />}
              {loading ? 'Analyzing…' : 'Run Inspection'}
            </button>

            {result && (
              <>
                <span style={{ width: 1, height: 22, background: '#1e293b' }} />
                <button className="btn btn-sm" onClick={handleDownloadPDF}>
                  <FileDown width={14} height={14} /> PDF
                </button>
                <button className="btn btn-sm" onClick={handleDownloadExcel}>
                  <Download width={14} height={14} /> XLSX
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Status banners */}
      {result && reviewState === 'ERROR' && (
        <div className="alert alert--danger" role="alert">
          <XOctagon width={20} height={20} style={{ marginTop: 2 }} />
          <div>
            <b>Inspection FAILED — pipeline error.</b>
            <p style={{ margin: '4px 0 0', color: '#cbd5e1' }}>
              The inference pipeline did not produce a result for this image. No score is available —
              this is an execution failure, not a clean board.
            </p>
            {(result.pipeline_warnings?.length ?? 0) > 0 && (
              <ul>
                {result.pipeline_warnings!.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            )}
          </div>
        </div>
      )}

      {result && reviewState === 'REVIEW_REQUIRED' && (
        <div className="alert alert--warning" role="alert">
          <AlertTriangle width={20} height={20} style={{ marginTop: 2 }} />
          <div>
            <b>REVIEW REQUIRED — zero detections, result not trusted.</b>
            <p style={{ margin: '4px 0 0', color: '#cbd5e1' }}>
              Both detectors returned zero results on a non-trivial image. A genuinely clean board cannot
              be distinguished from a silent detection failure. Score is deliberately withheld.
            </p>
            {(result.pipeline_warnings?.length ?? 0) > 0 && (
              <ul>
                {result.pipeline_warnings!.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            )}
          </div>
        </div>
      )}

      {result && reviewState === 'SUCCESS' && quality && (
        <div
          role="status"
          className={`alert alert--${quality.status === 'PASS' ? 'success' : quality.status.includes('REWORK') ? 'warning' : 'danger'}`}
        >
          {quality.status === 'PASS' ? <CheckCircle width={20} height={20} /> : <AlertTriangle width={20} height={20} />}
          <div>
            <b>Inspection complete — {quality.status}.</b>
            <p style={{ margin: '4px 0 0', color: '#cbd5e1' }}>
              {componentCount > 0 && defectCount === 0
                ? `${componentCount} components detected, zero defects. Pipeline execution is confirmed because components were found.`
                : `${defectCount} defect(s) across ${componentCount} component(s).`}
            </p>
          </div>
        </div>
      )}

      {/* ============================================================
         WIDESCREEN PCB VIEWER — FULL WIDTH, 16:9 landscape
         Same shell structure regardless of state (empty / upload preview / result).
         ============================================================ */}
      <div className="viewer-shell">
        <div className="viewer-toolbar">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <ScanLine width={16} height={16} style={{ color: '#60a5fa' }} />
            <span style={{ fontWeight: 600, color: '#cbd5e1', fontSize: 13 }}>
              {result ? 'Inspection Result' : previewUrl ? 'Loaded PCB Image' : 'PCB Viewer'}
            </span>
            {selectedFile && (
              <span className="mono" style={{ fontSize: 11.5, color: '#64748b' }}>
                {selectedFile.name}
                {result?.image_dimensions
                  ? ` · ${result.image_dimensions.width}×${result.image_dimensions.height}px`
                  : ''}
              </span>
            )}
          </div>

          {result && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 11.5, color: '#94a3b8', fontWeight: 600 }}>
                <Layers width={13} height={13} /> Overlays
              </span>
              <button
                onClick={() => setShowComponents(!showComponents)}
                className="btn btn-xs"
                style={showComponents ? { background: 'rgba(37,99,235,0.18)', color: '#93c5fd', borderColor: 'rgba(37,99,235,0.55)' } : {}}
              >
                Components ({componentCount})
              </button>
              <button
                onClick={() => setShowDefects(!showDefects)}
                className="btn btn-xs"
                style={showDefects ? { background: 'rgba(190,18,60,0.2)', color: '#fda4af', borderColor: 'rgba(226,29,72,0.55)' } : {}}
              >
                Defects ({defectCount})
              </button>
              <button
                onClick={() => setShowAttribution(!showAttribution)}
                className="btn btn-xs"
                style={showAttribution ? { background: 'rgba(147,51,234,0.22)', color: '#d8b4fe', borderColor: 'rgba(168,85,247,0.55)' } : {}}
                disabled={!result.xai?.overlay_base64}
                title={!result.xai?.overlay_base64 ? 'Overlay produced only when at least one defect is detected' : ''}
              >
                Heatmap {result.xai?.overlay_base64 ? '· On' : '· Unavailable'}
              </button>
            </div>
          )}

          {result && showAttribution && result.xai?.overlay_base64 && (
            <span
              title="Attribution overlay is produced by a heuristic approximation, not gradient backprop."
              className="status-chip"
              style={{ color: '#c084fc', borderColor: 'rgba(168,85,247,0.45)', background: 'rgba(147,51,234,0.12)' }}
            >
              {attributionBadge}
            </span>
          )}
        </div>

        <div className="viewer-frame">
          {viewerImgSrc ? (
            <img src={viewerImgSrc} alt={viewerImgAlt} />
          ) : (
            <div className="viewer-empty">
              <div className="viewer-empty-icon">
                <Upload width={26} height={26} />
              </div>
              <h3>No PCB Image Loaded</h3>
              <p>
                Upload a high-resolution industrial PCB image or use the <b>Load Demo Board</b>
                dropdown above, then click <b>Run Inspection</b>. Results appear in this viewer
                and full metrics populate the panels below.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* ============================================================
         DETAILS PANELS — BELOW THE VIEWER (not a right sidebar)
         ============================================================ */}
      {result ? (
        <>
          {/* KPI strip — 4 tiles */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14 }}>
            <div className={`kpi kpi--${statusKpiTone(quality)}`}>
              <span className="kpi-label"><Gauge width={12} height={12} style={{ verticalAlign: -2 }} /> Inspection Quality Score</span>
              {quality && typeof quality.overall_score === 'number' ? (
                <>
                  <div className="kpi-value">{quality.overall_score}<span style={{ fontSize: 15, color: '#64748b', marginLeft: 4 }}>/100</span></div>
                  <span className={`kpi-badge kpi-badge--${quality.status === 'PASS' ? 'pass' : quality.status.includes('REWORK') ? 'rework' : 'fail'}`}>
                    {quality.grade} · {quality.status}
                  </span>
                </>
              ) : (
                <>
                  <div className="kpi-value" style={{ fontSize: 20 }}>Score Withheld</div>
                  <span className="kpi-badge kpi-badge--review">{reviewState === 'ERROR' ? 'ERROR' : 'REVIEW REQUIRED'}</span>
                </>
              )}
              <span className="kpi-sub">{quality?.summary || 'Score unavailable for this run.'}</span>
            </div>

            <div className={`kpi kpi--${defectCount === 0 && reviewState === 'SUCCESS' ? 'success' : defectCount === 0 ? 'warning' : 'danger'}`}>
              <span className="kpi-label"><AlertTriangle width={12} height={12} style={{ verticalAlign: -2 }} /> Defects Found</span>
              <div className="kpi-value">{defectCount}</div>
              <span className="kpi-sub">
                {quality
                  ? `Defect risk: ${quality.defect_risk} · Component integrity: ${quality.component_integrity}/100`
                  : 'No score computed for this run.'}
              </span>
            </div>

            <div className="kpi kpi--info">
              <span className="kpi-label"><Target width={12} height={12} style={{ verticalAlign: -2 }} /> Components Confirmed</span>
              <div className="kpi-value">{componentCount}</div>
              <span className="kpi-sub">
                {result.components.length > 0
                  ? `${new Set(result.components.map((c) => c.class)).size} unique part types`
                  : 'No components detected this run.'}
              </span>
            </div>

            <div className="kpi kpi--info">
              <span className="kpi-label"><Zap width={12} height={12} style={{ verticalAlign: -2 }} /> Pipeline Latency</span>
              <div className="kpi-value">{fmtTime(result.inference_time_ms)}</div>
              <span className="kpi-sub">
                Run {fmtDate(result.timestamp)}<br />
                ID:&nbsp;
                <span className="mono" style={{ fontSize: 11 }}>
                  {(result.inspection_id || '').length > 14
                    ? (result.inspection_id.slice(0, 6) + '…' + result.inspection_id.slice(-5))
                    : (result.inspection_id || '—')}
                </span>
              </span>
            </div>
          </div>

          {/* Row A: Defects + Quality summary */}
          <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1.25fr) minmax(0,1fr)', gap: 16 }}>
            {/* Detected Defects */}
            <div className="panel">
              <div className="panel-header">
                <h4 className="panel-title">
                  <AlertTriangle width={15} height={15} style={{ color: '#fb7185' }} />
                  Detected Defects ({defectCount})
                </h4>
                <span className="mono" style={{ fontSize: 11, color: '#64748b' }}>
                  {quality ? `Risk profile: ${quality.defect_risk}` : ''}
                </span>
              </div>
              <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 10, maxHeight: 520, overflowY: 'auto' }}>
                {result.defects.length > 0 ? (
                  result.defects.map((d) => (
                    <div
                      key={d.id}
                      className={`defect-item ${selectedItem?.id === d.id ? 'is-selected' : ''}`}
                      onClick={() => setSelectedItem(d)}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <span className="defect-severity-dot" style={{ color: d.severity.color || '#f43f5e' }} />
                        <div>
                          <div className="defect-class">{d.class}</div>
                          <div className="defect-meta">
                            Confidence {Math.round(d.confidence * 100)}% · Near: {d.near_component || 'Ground plane'}
                          </div>
                        </div>
                      </div>
                      <div style={{ gridColumn: '3 / 4' }}>
                        <span className="defect-chip" data-lvl={d.severity.level}>
                          {d.severity.level} · {d.severity.score}
                        </span>
                      </div>
                      {selectedItem?.id === d.id && (
                        <div style={{ gridColumn: '1 / -1', fontSize: 12, color: '#94a3b8', lineHeight: 1.5, paddingTop: 2, borderTop: '1px dashed #1e293b' }}>
                          {d.severity.explanation || 'Severity is project-defined — not an IPC numeric score.'}
                        </div>
                      )}
                    </div>
                  ))
                ) : reviewState === 'REVIEW_REQUIRED' ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '24px 10px', color: '#fbbf24', fontSize: 12.5, fontWeight: 600, justifyContent: 'center' }}>
                    <AlertTriangle width={18} height={18} />
                    Zero defects returned — but this result is not trusted. See review notice above.
                  </div>
                ) : reviewState === 'ERROR' ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '24px 10px', color: '#fb7185', fontSize: 12.5, fontWeight: 600, justifyContent: 'center' }}>
                    <XOctagon width={18} height={18} />
                    Inspection failed — no detection data exists.
                  </div>
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '24px 10px', color: '#6ee7b7', fontSize: 12.5, fontWeight: 600, justifyContent: 'center' }}>
                    <CheckCircle width={18} height={18} />
                    No defects detected. {componentCount} components confirmed the pipeline executed.
                  </div>
                )}
              </div>
            </div>

            {/* Quality telemetry + components */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div className="panel">
                <div className="panel-header">
                  <h4 className="panel-title">
                    <Gauge width={15} height={15} style={{ color: '#60a5fa' }} />
                    Quality Telemetry
                  </h4>
                  <span className="mono" style={{ fontSize: 11, color: '#64748b' }}>
                    Contract v{result.contract_version || '1.0'}
                  </span>
                </div>
                <div className="panel-body">
                  <dl style={{ display: 'grid', gridTemplateColumns: '150px 1fr', rowGap: 10, columnGap: 14, fontSize: 13 }}>
                    <dt style={{ color: '#64748b', fontWeight: 600 }}>Overall Status</dt>
                    <dd>
                      <span className={`kpi-badge kpi-badge--${quality?.status === 'PASS' ? 'pass' : quality?.status.includes('REWORK') ? 'rework' : quality ? 'fail' : 'review'}`}>
                        {quality?.status || (reviewState === 'ERROR' ? 'ERROR' : 'REVIEW REQUIRED')}
                      </span>
                      <span style={{ marginLeft: 10, color: '#cbd5e1' }}>Grade {quality?.grade || '—'}</span>
                    </dd>

                    <dt style={{ color: '#64748b', fontWeight: 600 }}>Score (project-defined)</dt>
                    <dd className="mono" style={{ color: '#f1f5f9' }}>
                      {quality && typeof quality.overall_score === 'number'
                        ? `${quality.overall_score} / 100${quality.formula ? `  ·  ${quality.formula}` : ''}`
                        : 'Withheld (ambiguous zero-detection state)'}
                    </dd>

                    <dt style={{ color: '#64748b', fontWeight: 600 }}>Defect Risk</dt>
                    <dd style={{ color: '#cbd5e1' }}>{quality?.defect_risk || '—'}</dd>

                    <dt style={{ color: '#64748b', fontWeight: 600 }}>Component Integrity</dt>
                    <dd className="mono" style={{ color: '#cbd5e1' }}>
                      {quality ? `${quality.component_integrity} / 100` : '—'}
                    </dd>

                    <dt style={{ color: '#64748b', fontWeight: 600 }}>Summary</dt>
                    <dd style={{ color: '#cbd5e1', lineHeight: 1.5 }}>
                      {quality?.summary || 'Not computed.'}
                    </dd>
                  </dl>

                  {reviewState !== 'REVIEW_REQUIRED' && (result.pipeline_warnings?.length ?? 0) > 0 && (
                    <div style={{ marginTop: 16, padding: 12, borderRadius: 6, border: '1px solid rgba(217,119,6,0.45)', background: 'rgba(180,83,9,0.14)', fontSize: 12, color: '#fbbf24' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 700, marginBottom: 4 }}>
                        <Info width={13} height={13} /> Pipeline Warnings ({result.pipeline_warnings!.length})
                      </div>
                      <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.55 }}>
                        {result.pipeline_warnings!.map((w, i) => <li key={i}>{w}</li>)}
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              <div className="panel">
                <div className="panel-header">
                  <h4 className="panel-title">
                    <Layers width={15} height={15} style={{ color: '#93c5fd' }} />
                    Components on Board ({componentCount})
                  </h4>
                </div>
                <div className="panel-body">
                  {componentCount === 0 ? (
                    <div style={{ padding: '16px 10px', fontSize: 12.5, color: '#94a3b8' }}>
                      No component detections were returned for this image.
                    </div>
                  ) : (
                    <table className="tbl">
                      <thead>
                        <tr>
                          <th style={{ width: '44%' }}>Part</th>
                          <th>Count</th>
                          <th style={{ textAlign: 'right' }}>Avg. confidence</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(() => {
                          const grp = new Map<string, { count: number; sum: number }>();
                          result.components.forEach((c) => {
                            const key = c.class;
                            const cur = grp.get(key) || { count: 0, sum: 0 };
                            cur.count += 1;
                            cur.sum += c.confidence;
                            grp.set(key, cur);
                          });
                          return Array.from(grp.entries())
                            .sort((a, b) => b[1].count - a[1].count)
                            .map(([part, { count, sum }]) => (
                              <tr key={part}>
                                <td style={{ textTransform: 'capitalize', fontWeight: 600 }}>{part}</td>
                                <td className="mono">{count}</td>
                                <td style={{ textAlign: 'right' }} className="mono">
                                  {Math.round((sum / count) * 100)}%
                                </td>
                              </tr>
                            ));
                        })()}
                      </tbody>
                    </table>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Row B: Recommendations + Run metadata */}
          <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1.25fr) minmax(0,1fr)', gap: 16 }}>
            {/* Recommended actions */}
            <div className="panel">
              <div className="panel-header">
                <h4 className="panel-title">
                  <Wrench width={15} height={15} style={{ color: '#fbbf24' }} />
                  Engineering Guidance
                </h4>
                <span style={{ fontSize: 11, color: '#64748b' }}>
                  Static expert-curated rules — not model-generated output
                </span>
              </div>
              <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: 14, maxHeight: 520, overflowY: 'auto' }}>
                {(result.recommendations?.length ?? 0) === 0 ? (
                  <div style={{ padding: '20px 6px', fontSize: 13, color: '#94a3b8' }}>
                    No recommendations applicable for this run.
                  </div>
                ) : (
                  result.recommendations.map((r, idx) => (
                    <div className="rec-card" key={idx}>
                      <h5>
                        <AlertTriangle width={14} height={14} style={{ color: '#fb7185' }} />
                        {r.title}
                      </h5>
                      <dl style={{ margin: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
                        <div className="rec-row">
                          <dt>Probable Causes</dt>
                          <dd>
                            <ul>
                              {(r.probable_causes?.length ?? 0) > 0
                                ? r.probable_causes!.map((p, pi) => <li key={pi}>{p}</li>)
                                : <li>Not catalogued.</li>}
                            </ul>
                          </dd>
                        </div>
                        <div className="rec-row">
                          <dt>Inspection</dt>
                          <dd>
                            <ul>
                              {(r.inspection_steps?.length ?? 0) > 0
                                ? r.inspection_steps!.map((p, pi) => <li key={pi}>{p}</li>)
                                : <li>Inspect under 20× magnification with side lighting.</li>}
                            </ul>
                          </dd>
                        </div>
                        <div className="rec-row">
                          <dt>Repair</dt>
                          <dd>
                            <ul>
                              {(r.repair_actions?.length ?? 0) > 0
                                ? r.repair_actions!.map((p, pi) => <li key={pi}>{p}</li>)
                                : <li>Refer to technician desk instructions.</li>}
                            </ul>
                          </dd>
                        </div>
                        <div className="rec-row">
                          <dt>Verify</dt>
                          <dd>
                            <ul>
                              {(r.verification_steps?.length ?? 0) > 0
                                ? r.verification_steps!.map((p, pi) => <li key={pi}>{p}</li>)
                                : <li>Re-scan board after repair and confirm zero defects.</li>}
                            </ul>
                          </dd>
                        </div>
                      </dl>
                      {(r.safety_notes?.length ?? 0) > 0 && (
                        <div style={{ padding: '8px 10px', borderRadius: 5, fontSize: 11.5, color: '#fca5a5', background: 'rgba(127,29,29,0.25)', border: '1px dashed rgba(251,113,133,0.3)' }}>
                          <b>Safety · </b>{r.safety_notes!.join('  ·  ')}
                        </div>
                      )}
                      <div className="rec-ref">Reference guidance · {r.ipc_standard || 'Internal SOP'}</div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Run metadata + attribution */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div className="panel">
                <div className="panel-header">
                  <h4 className="panel-title">
                    <Clock width={15} height={15} style={{ color: '#93c5fd' }} />
                    Inspection Run
                  </h4>
                </div>
                <div className="panel-body">
                  <dl style={{ display: 'grid', gridTemplateColumns: '140px 1fr', rowGap: 9, columnGap: 12, fontSize: 12.5 }}>
                    <dt style={{ color: '#64748b', fontWeight: 600 }}>Inspection ID</dt>
                    <dd className="mono" style={{ wordBreak: 'break-all', color: '#cbd5e1' }}>
                      {result.inspection_id}
                    </dd>
                    <dt style={{ color: '#64748b', fontWeight: 600 }}>Image ID</dt>
                    <dd className="mono" style={{ wordBreak: 'break-all', color: '#cbd5e1' }}>
                      {result.image_id || '—'}
                    </dd>
                    <dt style={{ color: '#64748b', fontWeight: 600 }}>Timestamp</dt>
                    <dd style={{ color: '#cbd5e1' }}>{fmtDate(result.timestamp)}</dd>
                    <dt style={{ color: '#64748b', fontWeight: 600 }}>Processing Time</dt>
                    <dd className="mono" style={{ color: '#cbd5e1' }}>{fmtTime(result.inference_time_ms)}</dd>
                    <dt style={{ color: '#64748b', fontWeight: 600 }}>Input File</dt>
                    <dd style={{ color: '#cbd5e1', wordBreak: 'break-word' }}>
                      {selectedFile?.name || result.image_path || '—'}
                    </dd>
                    <dt style={{ color: '#64748b', fontWeight: 600 }}>Dimensions</dt>
                    <dd className="mono" style={{ color: '#cbd5e1' }}>
                      {result.image_dimensions ? `${result.image_dimensions.width} × ${result.image_dimensions.height} px` : '—'}
                    </dd>
                    <dt style={{ color: '#64748b', fontWeight: 600 }}>Pipeline Status</dt>
                    <dd>
                      <span className={`kpi-badge kpi-badge--${result.inspection_status === 'SUCCESS' ? 'pass' : 'fail'}`}>
                        {result.inspection_status || 'SUCCESS'}
                      </span>
                    </dd>
                  </dl>
                </div>
              </div>

              <div className="panel">
                <div className="panel-header">
                  <h4 className="panel-title">
                    <ScanLine width={15} height={15} style={{ color: '#a78bfa' }} />
                    Detection Models Used
                  </h4>
                </div>
                <div className="panel-body">
                  <dl style={{ display: 'grid', gridTemplateColumns: '140px 1fr', rowGap: 9, columnGap: 12, fontSize: 12.5 }}>
                    <dt style={{ color: '#64748b', fontWeight: 600 }}>Checkpoints</dt>
                    <dd className="mono" style={{ wordBreak: 'break-word', lineHeight: 1.5, color: '#cbd5e1' }}>
                      {formatModelVersion(result.model_version)}
                    </dd>
                    <dt style={{ color: '#64748b', fontWeight: 600 }}>Inference Device</dt>
                    <dd style={{ color: '#cbd5e1' }}>
                      {typeof result.model_version === 'object' && result.model_version
                        ? (result.model_version.inference_device || 'not reported')
                        : 'not reported'}
                    </dd>
                    <dt style={{ color: '#64748b', fontWeight: 600 }}>Threshold</dt>
                    <dd className="mono" style={{ color: '#cbd5e1' }}>{Math.round(confThreshold * 100)}%</dd>
                    <dt style={{ color: '#64748b', fontWeight: 600 }}>Models Available</dt>
                    <dd style={{ color: '#cbd5e1' }}>
                      {result.models_available === true ? 'Yes' : result.models_available === false ? 'No' : 'Not reported'}
                    </dd>
                  </dl>
                </div>
              </div>

              {result.xai && (
                <div className="panel">
                  <div className="panel-header">
                    <h4 className="panel-title">
                      <Eye width={15} height={15} style={{ color: '#c084fc' }} />
                      Attribution Overlay
                    </h4>
                  </div>
                  <div className="panel-body" style={{ fontSize: 12.5, lineHeight: 1.6, display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <div>
                      <b style={{ color: '#cbd5e1' }}>Method:&nbsp;</b>
                      <span className="mono">{result.xai.attribution_method || 'not reported'}</span>
                    </div>
                    <div style={{ color: '#cbd5e1' }}>
                      {result.xai.error || result.xai.interpretation || 'No attribution produced for this run (overlay runs when at least one defect is detected).'}
                    </div>
                    {result.xai.disclaimer && (
                      <div style={{ padding: '9px 11px', borderRadius: 5, background: '#050b18', border: '1px solid #1e293b', color: '#94a3b8', fontSize: 11.5 }}>
                        {result.xai.disclaimer}
                      </div>
                    )}
                    {result.xai.explained_class && (
                      <div>
                        <b style={{ color: '#cbd5e1' }}>Current defect:&nbsp;</b>
                        <span style={{ textTransform: 'capitalize', color: '#cbd5e1' }}>{result.xai.explained_class}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      ) : (
        /* No result yet — empty state banner panel */
        <div className="panel">
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14, padding: 22 }}>
            <div style={{ width: 40, height: 40, borderRadius: 8, background: '#0f172a', border: '1px solid #1e293b', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', flexShrink: 0 }}>
              <ShieldAlert width={20} height={20} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <div style={{ fontWeight: 600, color: '#e2e8f0' }}>Awaiting Inspection</div>
              <div style={{ color: '#64748b', fontSize: 13, lineHeight: 1.6 }}>
                Load an image and click <b>Run Inspection</b>. Once complete:
                <ul style={{ margin: '6px 0 0', paddingLeft: 20 }}>
                  <li>The viewer above shows annotated results with togglable overlays.</li>
                  <li>The <b>KPI strip</b> reports score, defect count, components, and latency.</li>
                  <li>The <b>panels below</b> list individual defects, quality telemetry, component inventory, engineering guidance, and run metadata.</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      <style>{`@keyframes spin { from { transform: rotate(0); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
};
