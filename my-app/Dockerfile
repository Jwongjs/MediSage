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
RUN npm run build
# Result: /app/dist contains the built static files (HTML, JS, CSS, assets).

# ── Stage 2: Serve ────────────────────────────────────────────────────────────
# Start completely fresh — zero Node, zero npm, zero source code in final image.
# nginx:alpine is ~20MB. The final image will be ~25MB total.
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
