# SmartPCB-XAI — React Industrial Frontend (Vite + TypeScript + Tailwind)
# Multi-stage build:
#   Stage 1 (builder): Node 20 -> npm install + npm run build -> /app/dist
#   Stage 2 (runtime): Nginx alpine -> serve dist/ on port 3000 (not 80, matches compose)

FROM node:20-alpine AS builder

ENV NODE_ENV=production \
    VITE_BACKEND_URL=http://localhost:5000

WORKDIR /app

COPY frontend/package.json        /app/package.json
COPY frontend/package-lock.json*  /app/
RUN npm ci || npm install

COPY frontend/             /app/
RUN npm run build

# ---- Serve stage ----
FROM nginx:1.27-alpine AS runner

# Copy compiled bundle output
COPY --from=builder /app/dist /usr/share/nginx/html

# Custom nginx config: listen on 3000 (not default 80), SPA fallback for React Router,
# pass /api upstream via env if needed, and proper content-type for .js / .mjs / .ts
RUN printf 'server {\n\
    listen       3000;\n\
    server_name  _;\n\
    root   /usr/share/nginx/html;\n\
    index  index.html index.htm;\n\
    # Single-page app fallback (client-side routing)\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
    # Cache compiled assets for long time, HTML short\n\
    location ~* \\.(?:js|mjs|css|png|jpg|jpeg|gif|svg|ico|woff2?)$ {\n\
        expires 7d;\n\
        add_header Cache-Control "public, max-age=604800, immutable";\n\
    }\n\
    location ~* \\.html$ {\n\
        expires -1;\n\
        add_header Cache-Control "no-cache, no-store";\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD wget -qO- http://127.0.0.1:3000/ >/dev/null 2>&1 || exit 1

CMD ["nginx", "-g", "daemon off;"]
