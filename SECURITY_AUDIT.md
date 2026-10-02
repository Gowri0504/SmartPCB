# SECURITY & AUTH AUDIT — 2026-09-23

Scope: Express backend (`backend/server.js`), FastAPI service
(`ai_service/main.py`), report generation. Verified by code review plus live
HTTP tests on 2026-09-23 (backend on :5000, FastAPI on :8000, MongoDB
127.0.0.1:27017).

## Verified working (live tests this session)

1. **JWT auth**: POST /api/auth/register issues a signed token (HS256,
   7-day expiry); GET /api/auth/me with `Authorization: Bearer <token>`
   returns the user. Verified 200.
2. **Privilege-escalation guard**: self-registration accepts only
   ENGINEER / INSPECTOR. POST register with role=ADMIN → **HTTP 403**
   "The 'ADMIN' role must be assigned by an existing administrator."
   Verified live.
3. **Role gate**: `requireRole(...)` middleware runs after authMiddleware and
   returns 401/403 appropriately.
4. **Upload validation**: multer fileFilter accepts only image types
   (jpg/jpeg/png/bmp/webp by mimetype or extension), 25 MB size cap,
   randomized server-side filenames (no original-name path traversal).
   Non-image uploads are rejected.
5. **CORS allowlist**: only origins in CORS_ORIGIN (default: local Vite
   dev server) or same-origin requests are allowed; configurable via env.
6. **Error hygiene**: `sendServerError` logs server-side with a correlation
   reference (SRV-…) and returns only a generic message — no stack traces,
   driver errors, or validation internals leak to clients. FastAPI likewise
   returns exception type+message only; tracebacks stay in server logs.
7. **Demo login disabled** by default (explicit 403 with guidance).
8. **Feedback input validation**: inspection_id/target_id/item_type required;
   item_type restricted to component|defect (400 otherwise).

## Known limitations (disclosed, not hidden)

1. **JWT_SECRET fallback**: if env JWT_SECRET is unset, a hardcoded
   development-only key is used (clearly labeled in code). Production MUST set
   JWT_SECRET; until then the deployment is not production-safe.
2. **No rate limiting** on /api/auth/login or any route — brute-force
   protection is absent.
3. **/uploads is a public static route** — uploaded board images are
   accessible without authentication to anyone who can reach the server.
4. **No HTTPS/TLS termination** in the dev servers; tokens travel in plaintext
   headers on localhost.
5. **Stateless JWT logout**: /api/auth/logout cannot revoke tokens (documented
   in code); a leaked token remains valid up to expiry.

## Privacy note

Uploaded PCB imagery may contain proprietary board designs; the public
/uploads route (limitation 3) is the highest-priority fix before any
network-exposed deployment.
