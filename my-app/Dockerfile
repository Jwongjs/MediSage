# ── Stage 1: Build ────────────────────────────────────────────────────────────
# node:20-alpine is the smallest Node image (~50MB).
# We only need Node here to run `npm run build` — it is not in the final image.
FROM node:20-alpine AS builder
WORKDIR /app

COPY package*.json ./
# npm ci reads package-lock.json exactly (no version drift).
# Always use `ci` in Docker/CI instead of `npm install` for reproducible builds.
RUN npm ci

COPY . .
# VITE_* vars are baked in at BUILD time. Docker needs an explicit ARG to receive
# Railway's service variable, and ENV to expose it to `vite build`. Without this,
# import.meta.env.VITE_API_URL is undefined -> API_BASE_URL='' -> API calls go to
# the frontend's own origin (405/HTML) instead of the backend. Empty default keeps
# local `docker build` working (falls back to the Vite dev proxy).
ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build
# Result: /app/dist contains the built static files (HTML, JS, CSS, assets).

# ── Stage 2: Serve ────────────────────────────────────────────────────────────
# Start completely fresh — zero Node, zero npm, zero source code in final image.
# nginx:alpine is ~20MB. The final image will be ~25MB total.
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html

# Railway injects $PORT and healthchecks it; nginx must listen there, not a
# hardcoded 80. The nginx:alpine entrypoint runs envsubst over
# /etc/nginx/templates/*.template -> /etc/nginx/conf.d/ at startup.
# NGINX_ENVSUBST_FILTER=PORT limits substitution to ${PORT} so nginx's own
# $uri variables are left intact. PORT defaults to 80 for local `docker run`.
COPY nginx.conf /etc/nginx/templates/default.conf.template
ENV PORT=80
ENV NGINX_ENVSUBST_FILTER=PORT
EXPOSE 80
