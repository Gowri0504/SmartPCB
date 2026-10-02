import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { MessageSquarePlus, RefreshCw, CheckCircle2, Database } from 'lucide-react';

interface FeedbackRecord {
  inspection_id: string;
  target_id: string;
  item_type: string;
  original_class?: string;
  corrected_class?: string;
  engineer_notes?: string;
  status?: string;
  timestamp?: string;
}

export const FeedbackView: React.FC = () => {
  const [inspectionId, setInspectionId] = useState('');
  const [targetId, setTargetId] = useState('');
  const [itemType, setItemType] = useState('defect');
  const [originalClass, setOriginalClass] = useState('');
  const [correctedClass, setCorrectedClass] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [feedbacks, setFeedbacks] = useState<FeedbackRecord[]>([]);

  useEffect(() => {
    fetchFeedbackList();
  }, []);

  const fetchFeedbackList = async () => {
    try {
      const res = await axios.get('/api/feedback');
      setFeedbacks(res.data);
    } catch (e: any) {
      console.warn("Feedback fetch error:", e.message);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setSuccess(null);
    setError(null);

    try {
      const res = await axios.post('/api/feedback', {
        inspection_id: inspectionId,
        target_id: targetId,
        item_type: itemType,
        original_class: originalClass,
        corrected_class: correctedClass,
        engineer_notes: notes
      });

      setSuccess(res.data?.message || 'Correction recorded in the Continuous Learning Data Collection Pipeline.');
      setOriginalClass('');
      setCorrectedClass('');
      setNotes('');
      fetchFeedbackList();
    } catch (err: any) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <Database className="w-5 h-5 text-indigo-400" />
          Continuous Learning Data Collection Pipeline
        </h3>
        <p className="text-xs text-slate-400 mt-1">
          Quality engineers can override an AI prediction. Validated corrections are stored in MongoDB as ground-truth
          annotations for <b>future offline retraining</b>. This pipeline collects data only — it does not retrain, fine-tune,
          or hot-swap the deployed model, and no automatic learning occurs at runtime.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Submission Form */}
        <div className="lg:col-span-5 bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
          <h4 className="text-sm font-bold text-slate-200">Record a Ground-Truth Correction</h4>

          {success && (
            <div className="bg-emerald-950/80 border border-emerald-800 text-emerald-300 p-3 rounded-lg text-xs flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
              <span>{success}</span>
            </div>
          )}
          {error && (
            <div className="bg-rose-950/80 border border-rose-800 text-rose-300 p-3 rounded-lg text-xs">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-400 mb-1">
                Inspection ID <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                required
                placeholder="INSP-… (from the Inspection Studio result panel)"
                value={inspectionId}
                onChange={e => setInspectionId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:border-blue-500 outline-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 mb-1">Target Type</label>
                <select
                  value={itemType}
                  onChange={e => setItemType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 outline-none"
                >
                  <option value="defect">Defect</option>
                  <option value="component">Component</option>
                </select>
              </div>
              <div>
                <label className="block text-slate-400 mb-1">
                  Target ID <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. D-1 or C-3"
                  value={targetId}
                  onChange={e => setTargetId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 outline-none"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 mb-1">Original Model Prediction</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. spur"
                  value={originalClass}
                  onChange={e => setOriginalClass(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 outline-none"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Correct Ground-Truth</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. short"
                  value={correctedClass}
                  onChange={e => setCorrectedClass(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Engineer Audit Rationale</label>
              <textarea
                rows={3}
                placeholder="Observed solder bridge bridging pad 2 and ground trace under stereo microscope..."
                value={notes}
                onChange={e => setNotes(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 outline-none"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg shadow-lg shadow-blue-600/30 transition flex items-center justify-center gap-2"
            >
              {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <MessageSquarePlus className="w-4 h-4" />}
              Save Correction for Offline Retraining
            </button>
          </form>
        </div>

        {/* Collected corrections list */}
        <div className="lg:col-span-7 bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl space-y-4">
          <h4 className="text-sm font-bold text-slate-200">
            Collected Corrections ({feedbacks.length} record{feedbacks.length === 1 ? '' : 's'})
          </h4>

          <div className="max-h-96 overflow-y-auto space-y-2.5">
            {feedbacks.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-12">
                No engineer corrections recorded yet. This list is read live from MongoDB — it is empty until a
                correction is submitted.
              </p>
            ) : (
              feedbacks.map((f, i) => (
                <div key={f.inspection_id + i} className="bg-slate-950 p-3.5 rounded-lg border border-slate-800 text-xs space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-slate-300">{f.target_id} ({f.item_type})</span>
                    <span className="text-[10px] bg-amber-950 text-amber-400 border border-amber-800/80 px-2 py-0.5 rounded font-mono">
                      {f.status || 'PENDING'}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 mono">inspection: {f.inspection_id}</p>
                  <p className="text-slate-400">
                    <span className="line-through text-rose-400 mr-2">{f.original_class}</span>
                    <span className="text-emerald-400 font-bold">&rarr; {f.corrected_class}</span>
                  </p>
                  {f.engineer_notes && <p className="text-slate-500 text-[11px] italic">"{f.engineer_notes}"</p>}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
