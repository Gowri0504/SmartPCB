import React, { useState } from 'react';
import { Cpu, AlertCircle, ShieldCheck, Crosshair, Wrench, Layers, XOctagon } from 'lucide-react';

/**
 * Digital Twin — spatial visualization of the MOST RECENT real inspection.
 *
 * This component holds NO sample/mock data. When no inspection has been run it
 * renders an explicit empty state; it never fabricates nodes. Data is passed
 * down from App.tsx, which receives it from the live /api/inspection/upload
 * response.
 */
interface DigitalTwinProps {
  inspectionData?: any;
  onNavigateToInspection?: () => void;
}

const getReviewState = (data: any): string => {
  if (!data) return 'NO_DATA';
  if (data.inspection_status === 'ERROR') return 'ERROR';
  if (data.review_required || data.suspicious_zero_detection) return 'REVIEW_REQUIRED';
  return 'SUCCESS';
};

export const DigitalTwin: React.FC<DigitalTwinProps> = ({ inspectionData, onNavigateToInspection }) => {
  const [activeItem, setActiveItem] = useState<any | null>(null);

  const components: any[] = inspectionData?.components || [];
  const defects: any[] = inspectionData?.defects || [];
  const reviewState = getReviewState(inspectionData);

  const imgW = inspectionData?.image_dimensions?.width || 0;
  const imgH = inspectionData?.image_dimensions?.height || 0;
  const hasDims = imgW > 0 && imgH > 0;

  // Normalized placement: bbox pixel coords -> % of actual image dimensions.
  // When dimensions are missing, positions fall back to the bbox coordinate
  // space directly (still real data, only the scale reference differs).
  const positionOf = (bbox: number[]) => {
    const x = (bbox[0] + bbox[2]) / 2;
    const y = (bbox[1] + bbox[3]) / 2;
    if (hasDims) return { left: `${(x / imgW) * 100}%`, top: `${(y / imgH) * 100}%` };
    const maxX = Math.max(1, ...components.concat(defects).map((n: any) => n.bbox?.[2] ?? 1));
    const maxY = Math.max(1, ...components.concat(defects).map((n: any) => n.bbox?.[3] ?? 1));
    return { left: `${(x / maxX) * 100}%`, top: `${(y / maxY) * 100}%` };
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex items-center justify-between shadow-xl">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Cpu className="w-5 h-5 text-cyan-400" />
            PCB Interactive Digital Twin (Visual Spatial Representation)
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Spatial mapping of the detected surface-mount components and defect locations from the most recent inspection.
          </p>
        </div>
        {inspectionData ? (
          <span className={`text-[11px] font-semibold px-3 py-1 rounded-full uppercase tracking-wider border ${
            reviewState === 'SUCCESS'
              ? 'bg-cyan-950 text-cyan-300 border-cyan-800/80'
              : reviewState === 'ERROR'
                ? 'bg-rose-950 text-rose-300 border-rose-800'
                : 'bg-amber-950 text-amber-300 border-amber-800'
          }`}>
            {reviewState === 'SUCCESS' ? 'Live Inspection Data' : reviewState === 'ERROR' ? 'Inspection Failed' : 'Result Under Review'}
          </span>
        ) : (
          <span className="text-[11px] font-semibold bg-slate-800 text-slate-400 border border-slate-700 px-3 py-1 rounded-full uppercase tracking-wider">
            No Inspection Loaded
          </span>
        )}
      </div>

      {!inspectionData ? (
        /* Explicit empty state — never render fabricated nodes */
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-10 text-center space-y-3">
          <Layers className="w-12 h-12 text-slate-600 mx-auto" />
          <p className="text-sm font-semibold text-slate-300">No inspection data available</p>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            The Digital Twin renders the detected components and defects of a real inspection. Run an inspection in the
            Inspection Studio first, then return to this tab.
          </p>
          {onNavigateToInspection && (
            <button
              onClick={onNavigateToInspection}
              className="mt-2 inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-xs font-semibold transition"
            >
              Go to Inspection Studio
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Virtual Board Canvas */}
          <div className="lg:col-span-8 bg-emerald-950/20 border border-emerald-800/40 rounded-xl p-6 relative flex flex-col items-center justify-center min-h-[520px] shadow-2xl overflow-hidden bg-[radial-gradient(#065f46_1px,transparent_1px)] [background-size:16px_16px]">
            <div className="absolute top-4 left-4 flex items-center gap-4 bg-slate-950/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-800 text-xs z-10">
              <span className="flex items-center gap-1.5 text-slate-300 font-medium">
                <span className="w-3 h-3 rounded-full bg-blue-500 inline-block"></span> Detected Component
              </span>
              <span className="flex items-center gap-1.5 text-slate-300 font-medium">
                <span className="w-3 h-3 rounded-full bg-rose-500 inline-block"></span> Detected Defect
              </span>
              {!hasDims && (
                <span className="flex items-center gap-1.5 text-amber-300 font-medium">
                  <AlertCircle className="w-3.5 h-3.5" /> Positions use relative bbox space (image dimensions not reported)
                </span>
              )}
            </div>

            <div className="relative w-[640px] h-[480px] bg-emerald-950/40 border-2 border-emerald-600/50 rounded-xl shadow-[0_0_50px_rgba(16,185,129,0.15)]">
              {(components.length + defects.length === 0) && (
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-8">
                  {reviewState === 'ERROR' ? (
                    <>
                      <XOctagon className="w-10 h-10 text-rose-400 mb-2" />
                      <p className="text-sm font-bold text-rose-300">Inspection failed — no nodes to map</p>
                      <p className="text-xs text-slate-500 mt-1">The pipeline did not produce detection data for this image.</p>
                    </>
                  ) : (
                    <>
                      <ShieldCheck className="w-10 h-10 text-emerald-400 mb-2" />
                      <p className="text-sm font-bold text-amber-300">Zero detections — result under review</p>
                      <p className="text-xs text-slate-500 mt-1 max-w-sm">
                        Both detectors returned zero results. The twin cannot distinguish a genuinely clean board from a
                        detection failure, so no nodes are rendered.
                      </p>
                    </>
                  )}
                </div>
              )}

              {/* Component Nodes */}
              {components.map((comp: any) => {
                const isSelected = activeItem?.id === comp.id;
                return (
                  <button
                    key={comp.id}
                    onClick={() => setActiveItem({ ...comp, type: "COMPONENT" })}
                    style={positionOf(comp.bbox)}
                    className={`absolute -translate-x-1/2 -translate-y-1/2 p-2 rounded-lg border flex items-center gap-1.5 text-xs font-bold transition shadow-lg ${
                      isSelected 
                        ? 'bg-blue-600 text-white border-white scale-110 z-20 shadow-blue-500/50' 
                        : 'bg-slate-900/90 text-blue-300 border-blue-500/60 hover:scale-105 hover:bg-slate-800'
                    }`}
                  >
                    <Cpu className="w-3.5 h-3.5" />
                    <span>{comp.class}</span>
                  </button>
                );
              })}

              {/* Defect Nodes */}
              {defects.map((def: any) => {
                const isSelected = activeItem?.id === def.id;
                return (
                  <button
                    key={def.id}
                    onClick={() => setActiveItem({ ...def, type: "DEFECT" })}
                    style={positionOf(def.bbox)}
                    className={`absolute -translate-x-1/2 -translate-y-1/2 p-2 rounded-lg border flex items-center gap-1.5 text-xs font-extrabold transition shadow-lg ${
                      isSelected 
                        ? 'bg-rose-600 text-white border-white scale-125 z-30 shadow-rose-500/50' 
                        : 'bg-rose-950/95 text-rose-300 border-rose-500 hover:scale-110'
                    }`}
                  >
                    <AlertCircle className="w-4 h-4 text-rose-400" />
                    <span>{def.class.toUpperCase()}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Right Detail Panel */}
          <div className="lg:col-span-4 space-y-4">
            {/* Inspection summary */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-xl text-xs space-y-1.5">
              <p className="text-slate-400"><b>Inspection:</b> <span className="mono break-all">{inspectionData.inspection_id}</span></p>
              <p className="text-slate-400"><b>Components:</b> <span className="mono text-blue-400">{components.length}</span> · <b>Defects:</b> <span className="mono text-rose-400">{defects.length}</span></p>
              {inspectionData.image_dimensions && hasDims && (
                <p className="text-slate-400"><b>Image:</b> <span className="mono">{imgW} × {imgH} px</span></p>
              )}
            </div>

            {activeItem ? (
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <Crosshair className="w-4 h-4 text-cyan-400" />
                    <h4 className="font-bold text-sm text-slate-200">
                      {activeItem.type === 'DEFECT' ? 'Defect Telemetry' : 'Component Details'}
                    </h4>
                  </div>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                    activeItem.type === 'DEFECT' ? 'bg-rose-950 text-rose-300 border border-rose-800' : 'bg-blue-950 text-blue-300 border border-blue-800'
                  }`}>
                    {activeItem.id}
                  </span>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Class Label:</span>
                    <span className="font-bold text-slate-200 uppercase">{activeItem.class}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Model Confidence:</span>
                    <span className="mono font-semibold text-emerald-400">{Math.round(activeItem.confidence * 100)}%</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Coordinates (Bounding Box):</span>
                    <span className="mono text-[11px] text-slate-300">[{activeItem.bbox.join(', ')}]</span>
                  </div>

                  {activeItem.type === 'DEFECT' && activeItem.severity && (
                    <>
                      <div className="flex justify-between py-1 border-b border-slate-800/60">
                        <span className="text-slate-400">Severity Classification:</span>
                        <span className="font-extrabold" style={{ color: activeItem.severity.color }}>
                          {activeItem.severity.level} ({activeItem.severity.score}/100)
                        </span>
                      </div>
                      <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-[11px] text-slate-400 leading-relaxed">
                        {activeItem.severity.explanation}
                      </div>
                    </>
                  )}
                </div>

                <div className="pt-2">
                  <button 
                    onClick={() => alert(`Marking ${activeItem.id} for physical verification.`)}
                    className="w-full flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 py-2 rounded-lg text-xs font-semibold border border-slate-700 transition"
                  >
                    <Wrench className="w-3.5 h-3.5 text-amber-400" />
                    Flag for Rework Bench
                  </button>
                </div>
              </div>
            ) : (
              <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-6 text-center space-y-3 text-slate-400">
                <Layers className="w-10 h-10 text-slate-600 mx-auto" />
                <p className="text-sm font-semibold text-slate-300">Select Any Digital Node</p>
                <p className="text-xs text-slate-500">
                  Click on any component or defect node on the virtual PCB board to inspect its coordinate telemetry, confidence score, and repair action.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
