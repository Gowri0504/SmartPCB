# SmartPCB-XAI — Express Application Backend (Node.js 20)
# Serves: MongoDB persistence, JWT auth, inspection upload (proxy to FastAPI),
#          analytics aggregation, feedback queue, and report proxy endpoints.
# Exposes port 5000.

FROM node:20-alpine AS base

ENV NODE_ENV=production \
    PORT=5000 \
    FASTAPI_URL=http://ai-service:8000 \
    MONGODB_URI=mongodb://mongodb:27017/smartpcb_xai \
    JWT_SECRET=override-in-production

WORKDIR /app

# Install npm deps first (cached layer)
COPY backend/package.json /app/package.json
COPY backend/package-lock.json* /app/
RUN npm ci --omit=dev || npm install --omit=dev

# Copy source
COPY backend/server.js         /app/server.js
COPY backend/models/           /app/models/
COPY backend/.env.example*     /app/.env.example 2>/dev/null || true
COPY backend/uploads/          /app/uploads/

# Ensure uploads directory exists for multer diskStorage
RUN mkdir -p /app/uploads

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD wget -qO- http://127.0.0.1:5000/api/health 2>/dev/null || node -e "require('http').get('http://127.0.0.1:5000/api/health', r => process.exit(r.statusCode===200?0:1)).on('error', ()=>process.exit(1))" || exit 1

CMD ["node", "server.js"]
