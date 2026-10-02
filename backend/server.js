const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const multer = require('multer');
const axios = require('axios');
const FormData = require('form-data');
const jwt = require('jsonwebtoken');

const User = require('./models/User');
const Inspection = require('./models/Inspection');
const Feedback = require('./models/Feedback');

const app = express();
const PORT = process.env.PORT || 5000;
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://127.0.0.1:8000';
const MONGO_URI = process.env.MONGO_URI || 'mongodb://127.0.0.1:27017/smartpcb_xai';
// DEVELOPMENT-ONLY FALLBACK. Production deployment MUST override via the
// JWT_SECRET environment variable. The fallback value below is a demo-only
// placeholder explicitly labeled INSECURE — never ship it to production.
const JWT_SECRET = process.env.JWT_SECRET || 'DEVELOPMENT-ONLY-INSECURE-smartpcb-xai-fallback-key';

// Middleware
// CORS origin is configurable via CORS_ORIGIN (comma-separated list). The dev
// default allows the local Vite dev server only; when the frontend is served
// from the same origin as this API (production build served by Express), no
// cross-origin access is needed at all.
const CORS_ORIGINS = (process.env.CORS_ORIGIN || 'http://localhost:5173,http://127.0.0.1:5173')
  .split(',').map(s => s.trim()).filter(Boolean);
app.use(cors({
  origin: (origin, cb) => {
    if (!origin || CORS_ORIGINS.includes(origin)) return cb(null, true);
    return cb(null, false);
  },
  credentials: true
}));
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Storage for uploaded images
const UPLOADS_DIR = path.join(__dirname, 'uploads');
if (!fs.existsSync(UPLOADS_DIR)) fs.mkdirSync(UPLOADS_DIR, { recursive: true });
app.use('/uploads', express.static(UPLOADS_DIR));

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, UPLOADS_DIR),
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname);
    cb(null, `PCB_${Date.now()}_${Math.round(Math.random()*1E6)}${ext}`);
  }
});
const upload = multer({ 
  storage,
  limits: { fileSize: 25 * 1024 * 1024 }, // 25 MB
  fileFilter: (req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase();
    const isImgExt = ['.jpg', '.jpeg', '.png', '.bmp', '.webp'].includes(ext);
    if (file.mimetype.startsWith('image/') || isImgExt) cb(null, true);
    else cb(new Error('Only image files (JPG, PNG, WEBP, BMP) are permitted.'), false);
  }
});

// MongoDB Connection
mongoose.connect(MONGO_URI)
  .then(() => console.log(`[MongoDB] Connected successfully to ${MONGO_URI}`))
  .catch(err => console.warn(`[MongoDB Warning] Failed to connect: ${err.message}. Operating with in-memory fallback if needed.`));

// Auth Middleware
const authMiddleware = (req, res, next) => {
  const token = req.headers['authorization']?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'Authentication token required.' });
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.user = decoded;
    next();
  } catch (err) {
    return res.status(403).json({ error: 'Invalid or expired authentication token.' });
  }
};

// Role gate. Must be used AFTER authMiddleware so req.user exists.
const requireRole = (...allowedRoles) => (req, res, next) => {
  if (!req.user) {
    return res.status(401).json({ error: 'Authentication token required.' });
  }
  if (!allowedRoles.includes(req.user.role)) {
    return res.status(403).json({
      error: `This action requires one of: ${allowedRoles.join(', ')}.`,
    });
  }
  next();
};

// Roles that may be granted through anonymous self-registration.
// ADMIN is deliberately excluded: otherwise any caller could POST
// {role:"ADMIN"} to /api/auth/register and escalate to full privileges.
const SELF_REGISTERABLE_ROLES = ['ENGINEER', 'INSPECTOR'];

// Never return raw internal error text (stack/driver/validation details) to
// clients; log server-side and answer with a generic message + correlation id.
let _errSeq = 0;
const sendServerError = (res, err, context) => {
  _errSeq += 1;
  const ref = `SRV-${Date.now().toString(36)}-${_errSeq}`;
  console.error(`[${context}] ref=${ref}`, err);
  if (res.headersSent) return;
  res.status(500).json({ error: `Internal server error. Reference: ${ref}` });
};

// ==========================================
// 1. AUTHENTICATION ROUTES
// ==========================================
app.post('/api/auth/register', async (req, res) => {
  try {
    const { name, email, password, role } = req.body;
    if (!name || !email || !password) {
      return res.status(400).json({ error: 'name, email and password are required.' });
    }
    // Anonymous self-registration may never mint a privileged account.
    const requestedRole = (role || 'ENGINEER').toString().toUpperCase();
    if (!SELF_REGISTERABLE_ROLES.includes(requestedRole)) {
      return res.status(403).json({
        error: `Self-registration is limited to: ${SELF_REGISTERABLE_ROLES.join(', ')}. ` +
               `The '${requestedRole}' role must be assigned by an existing administrator.`,
      });
    }
    let user = await User.findOne({ email });
    if (user) return res.status(400).json({ error: 'User already exists with this email.' });

    user = new User({ name, email, password, role: requestedRole });
    await user.save();

    const token = jwt.sign({ id: user._id, role: user.role, name: user.name }, JWT_SECRET, { expiresIn: '7d' });
    res.json({ token, user: { id: user._id, name: user.name, email: user.email, role: user.role } });
  } catch (err) {
    if (err && err.name === 'ValidationError') {
      return res.status(400).json({ error: 'Invalid registration payload.' });
    }
    return sendServerError(res, err, 'AUTH/register');
  }
});

app.post('/api/auth/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    if (!email || !password) {
      return res.status(400).json({ error: 'email and password are required.' });
    }
    const user = await User.findOne({ email });
    if (!user || !(await user.matchPassword(password))) {
      return res.status(401).json({ error: 'Invalid email or password.' });
    }
    const token = jwt.sign({ id: user._id, role: user.role, name: user.name }, JWT_SECRET, { expiresIn: '7d' });
    res.json({ token, user: { id: user._id, name: user.name, email: user.email, role: user.role } });
  } catch (err) {
    return sendServerError(res, err, 'AUTH/login');
  }
});

// Demo login previously issued a 7-day ADMIN token to any anonymous caller.
// It is now gated behind ALLOW_DEMO_LOGIN=1 and, when enabled, issues a
// non-privileged INSPECTOR token only. Default: disabled (403).
app.post('/api/auth/demo', (req, res) => {
  if (process.env.ALLOW_DEMO_LOGIN !== '1') {
    return res.status(403).json({
      error: 'Demo login is disabled. Use /api/auth/register or /api/auth/login.',
    });
  }
  const guestUser = { id: 'guest_001', name: 'Guest Inspector (Demo)', role: 'INSPECTOR', email: 'guest@smartpcb-xai.local' };
  const token = jwt.sign(guestUser, JWT_SECRET, { expiresIn: '1d' });
  res.json({ token, user: guestUser, warning: 'Demo login enabled via ALLOW_DEMO_LOGIN=1. Development use only.' });
});

// Validates a token and echoes the identity it carries. Useful to detect
// expiry client-side without attempting a privileged action first.
app.get('/api/auth/me', authMiddleware, (req, res) => {
  res.json({ user: { id: req.user.id, name: req.user.name, role: req.user.role } });
});

// JWTs are stateless, so the server has nothing to revoke. This endpoint exists
// so clients have one unambiguous place to end a session; it discards the token
// and tells the caller to delete it. It does NOT invalidate the token
// server-side — there is no revocation list in this implementation.
app.post('/api/auth/logout', authMiddleware, (req, res) => {
  res.json({
    status: 'LOGGED_OUT',
    note: 'Client must discard the token. Tokens are stateless and remain valid until expiry; ' +
          'no server-side revocation list is implemented.',
  });
});

// ==========================================
// 2. INSPECTION ROUTES
// ==========================================
app.post('/api/inspection/upload', upload.single('image'), async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ error: 'No image file uploaded.' });

    const localImagePath = req.file.path;
    const pcbId = req.body.pcb_id || `PCB-${Date.now().toString().slice(-6)}`;
    const confThresh = req.body.confidence_threshold || 0.25;

    // Call FastAPI AI Inference Engine
    const formData = new FormData();
    formData.append('file', fs.createReadStream(localImagePath));
    formData.append('confidence_threshold', confThresh);

    let aiResult;
    try {
      const response = await axios.post(`${FASTAPI_URL}/api/v1/inspect`, formData, {
        headers: { ...formData.getHeaders() }
      });
      aiResult = response.data;
    } catch (aiErr) {
      console.error('[AI Service Call Failed]', aiErr.message);
      return res.status(502).json({ error: `AI inference service error: ${aiErr.message}` });
    }

    // Save Inspection into MongoDB
    const aiSuccess = aiResult.inspection_status !== 'ERROR'
      && aiResult.quality_score !== null
      && aiResult.quality_score !== undefined;

    const inspectionDoc = new Inspection({
      contract_version: aiResult.contract_version || null,
      inspection_id: aiResult.inspection_id,
      inspection_status: aiResult.inspection_status || (aiSuccess ? 'SUCCESS' : 'ERROR'),
      image_id: aiResult.image_id || null,
      pcb_id: pcbId,
      image_path: `/uploads/${path.basename(localImagePath)}`,
      preview_image_base64: aiResult.preview_image_base64,
      model_version: aiResult.model_version || null,
      inference_time_ms: typeof aiResult.inference_time_ms === 'number' ? aiResult.inference_time_ms : null,
      image_dimensions: aiResult.image_dimensions,
      component_count: aiResult.component_count !== undefined
        ? aiResult.component_count
        : (aiResult.components || []).length,
      defect_count: aiResult.defect_count !== undefined
        ? aiResult.defect_count
        : (aiResult.defects || []).length,
      pipeline_warnings: aiResult.pipeline_warnings || [],
      suspicious_zero_detection: aiResult.suspicious_zero_detection || false,
      review_required: aiResult.review_required || false,
      models_available: aiResult.models_available !== undefined ? aiResult.models_available : null,
      severity: aiResult.severity || [],
      components: aiResult.components || [],
      defects: aiResult.defects || [],
      quality_score: aiSuccess ? aiResult.quality_score : null,
      recommendations: aiResult.recommendations || [],
      xai: aiResult.xai || {},
      inspector: req.user?.name || 'Automated AI Vision Engine'
    });

    try {
      await inspectionDoc.save();
    } catch (dbErr) {
      console.warn('[MongoDB Save Error]', dbErr.message);
    }

    res.json(inspectionDoc);
  } catch (err) {
    return sendServerError(res, err, 'INSPECTION/upload');
  }
});

app.get('/api/inspection/:id', async (req, res) => {
  try {
    const inspection = await Inspection.findOne({ inspection_id: req.params.id });
    if (!inspection) return res.status(404).json({ error: 'Inspection record not found.' });
    res.json(inspection);
  } catch (err) {
    return sendServerError(res, err, 'INSPECTION/get');
  }
});

app.get('/api/history', async (req, res) => {
  try {
    const limit = parseInt(req.query.limit) || 20;
    const inspections = await Inspection.find()
      .sort({ createdAt: -1 })
      .limit(limit)
      .select('inspection_id pcb_id quality_score defects components createdAt verification_status image_path');
    res.json(inspections);
  } catch (err) {
    return sendServerError(res, err, 'HISTORY/list');
  }
});

// ==========================================
// 3. ANALYTICS ROUTES
// ==========================================
app.get('/api/analytics', async (req, res) => {
  try {
    const totalInspections = await Inspection.countDocuments();
    const passed = await Inspection.countDocuments({ 'quality_score.status': 'PASS' });
    const rework = await Inspection.countDocuments({ 'quality_score.status': 'REWORK REQUIRED' });
    const failed = await Inspection.countDocuments({ 'quality_score.status': 'FAIL' });
    const reviewRequired = await Inspection.countDocuments({ 'quality_score.status': 'REVIEW_REQUIRED' });

    // Defect class aggregation
    const inspections = await Inspection.find().select('defects quality_score createdAt');
    const defectDistribution = {};
    let totalScoreSum = 0;
    let scoredCount = 0;

    inspections.forEach(insp => {
      const s = insp.quality_score?.overall_score;
      // Only inspections with a real computed score contribute to the average.
      // Withheld scores (REVIEW_REQUIRED / null) are excluded, never counted as 100.
      if (typeof s === 'number' && Number.isFinite(s)) {
        totalScoreSum += s;
        scoredCount += 1;
      }
      (insp.defects || []).forEach(d => {
        defectDistribution[d.class] = (defectDistribution[d.class] || 0) + 1;
      });
    });

    // Honest empty state: null means "no data yet", not a perfect score.
    const avgQuality = scoredCount > 0 ? Number((totalScoreSum / scoredCount).toFixed(1)) : null;
    const yieldRate = totalInspections > 0
      ? Number((((passed + rework) / totalInspections) * 100).toFixed(1))
      : null;

    res.json({
      total_inspections: totalInspections,
      pass_count: passed,
      rework_count: rework,
      fail_count: failed,
      review_required_count: reviewRequired,
      scored_inspection_count: scoredCount,
      yield_rate: yieldRate === null ? null : `${yieldRate}%`,
      average_quality_score: avgQuality,
      defect_distribution: defectDistribution,
      last_updated: new Date().toISOString()
    });
  } catch (err) {
    return sendServerError(res, err, 'ANALYTICS/summary');
  }
});

// ==========================================
// 4. CONTINUOUS LEARNING DATA COLLECTION PIPELINE
//    This endpoint collects corrected annotations for future offline model
//    retraining. No online/automatic retraining exists in this system; the
//    message below states that explicitly instead of implying live learning.
// ==========================================
app.post('/api/feedback', async (req, res) => {
  try {
    const { inspection_id, target_id, item_type, original_class, corrected_class, engineer_notes } = req.body;
    if (!inspection_id || !target_id || !item_type) {
      return res.status(400).json({ error: 'inspection_id, target_id and item_type are required.' });
    }
    if (!['component', 'defect'].includes(item_type)) {
      return res.status(400).json({ error: "item_type must be 'component' or 'defect'." });
    }
    const feedback = new Feedback({
      inspection_id,
      target_id,
      item_type,
      original_class,
      corrected_class,
      engineer_notes,
      submitted_by: req.user?.name || 'Engineer'
    });
    await feedback.save();

    // Mark inspection status as confirmed/reworked
    await Inspection.updateOne({ inspection_id }, { verification_status: 'CONFIRMED' });

    res.json({
      message: 'Correction recorded in the Continuous Learning Data Collection Pipeline. It is stored for future offline retraining; it does not modify the deployed model automatically.',
      feedback
    });
  } catch (err) {
    return sendServerError(res, err, 'FEEDBACK/submit');
  }
});

app.get('/api/feedback', async (req, res) => {
  try {
    const feedbacks = await Feedback.find().sort({ timestamp: -1 });
    res.json(feedbacks);
  } catch (err) {
    return sendServerError(res, err, 'FEEDBACK/list');
  }
});

// ==========================================
// 5. REPORT PROXIES (Forward to FastAPI)
// ==========================================
app.post('/api/reports/pdf', async (req, res) => {
  try {
    const resp = await axios.post(`${FASTAPI_URL}/api/v1/report/pdf`, req.body, { responseType: 'stream' });
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', 'attachment; filename="PCB_Inspection_Report.pdf"');
    resp.data.pipe(res);
  } catch (err) {
    return sendServerError(res, err, 'REPORTS/pdf');
  }
});

app.post('/api/reports/excel', async (req, res) => {
  try {
    const resp = await axios.post(`${FASTAPI_URL}/api/v1/report/excel`, req.body, { responseType: 'stream' });
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    res.setHeader('Content-Disposition', 'attachment; filename="PCB_Audit.xlsx"');
    resp.data.pipe(res);
  } catch (err) {
    return sendServerError(res, err, 'REPORTS/excel');
  }
});

// ==========================================
// 6. LIVE SYSTEM STATUS (no hardcoded badges in the UI)
//    Every field below is probed at request time. Nothing is assumed.
// ==========================================
app.get('/api/system-status', async (req, res) => {
  const mongoState = mongoose.connection.readyState;
  const mongoStates = { 0: 'disconnected', 1: 'connected', 2: 'connecting', 3: 'disconnecting' };
  let aiEngine = { reachable: false, detail: 'unreachable' };
  try {
    const r = await axios.get(`${FASTAPI_URL}/health`, { timeout: 4000 });
    aiEngine = { reachable: true, detail: r.data };
  } catch (err) {
    aiEngine = { reachable: false, detail: err.code || err.message };
  }
  res.json({
    express: { reachable: true, port: PORT },
    mongodb: { state: mongoStates[mongoState] || `unknown(${mongoState})`, connected: mongoState === 1 },
    ai_engine: aiEngine,
    checked_at: new Date().toISOString()
  });
});

// ==========================================
// 7. MODEL EVALUATION ARTIFACTS
//    Serves the on-disk evaluation artifacts verbatim. Missing artifacts are
//    reported as null with an explicit reason — the UI must render
//    "NOT VERIFIED" rather than a placeholder number.
// ==========================================
const REPO_ROOT = path.join(__dirname, '..');
const EVAL_ARTIFACTS = {
  inference_benchmark: path.join(REPO_ROOT, 'reports', 'benchmark', 'inference_benchmark.json'),
  component_metrics: path.join(REPO_ROOT, 'metrics', 'component_metrics.json'),
  defect_metrics: path.join(REPO_ROOT, 'metrics', 'defect_metrics.json'),
  component_class_report: path.join(REPO_ROOT, 'metrics', 'per_class_component.csv'),
  defect_class_report: path.join(REPO_ROOT, 'metrics', 'per_class_defect.csv'),
  full_pipeline_metrics: path.join(REPO_ROOT, 'metrics', 'full_pipeline_metrics.json'),
  pipeline_20_images_report: path.join(REPO_ROOT, 'metrics', 'pipeline_20_images_report.csv')
};

app.get('/api/model-evaluation', (req, res) => {
  const artifacts = {};
  for (const [key, filePath] of Object.entries(EVAL_ARTIFACTS)) {
    if (!fs.existsSync(filePath)) {
      artifacts[key] = { available: false, reason: 'NOT VERIFIED — no evaluation artifact has been generated on this machine.' };
      continue;
    }
    try {
      const stat = fs.statSync(filePath);
      const raw = fs.readFileSync(filePath, 'utf8');
      const isJson = filePath.endsWith('.json');
      artifacts[key] = {
        available: true,
        path: path.relative(REPO_ROOT, filePath).replace(/\\/g, '/'),
        size_bytes: stat.size,
        modified_at: stat.mtime.toISOString(),
        data: isJson ? JSON.parse(raw) : raw
      };
    } catch (err) {
      console.error(`[MODEL_EVAL/read] ${key}`, err);
      artifacts[key] = { available: false, reason: `Artifact exists but could not be read: ${err.message}` };
    }
  }
  res.json({ generated_at: new Date().toISOString(), artifacts });
});

// Unknown API route -> JSON 404 (never HTML error pages for API consumers)
app.use('/api', (req, res) => {
  res.status(404).json({ error: `Unknown API endpoint: ${req.method} ${req.originalUrl}` });
});

// Server Listen
app.listen(PORT, () => {
  console.log(`[SmartPCB Backend] Express server running on port ${PORT}`);
  console.log(`[SmartPCB Backend] Connected to FastAPI AI Engine at ${FASTAPI_URL}`);
});
