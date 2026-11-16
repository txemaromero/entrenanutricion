# syntax=docker/dockerfile:1
# Base images by digest (Dependabot proposes the new ones): the same bytes on every build.
FROM node:24.22.2-alpine@sha256:a34ab6d7f6f4813f4d0c5469d74685604b962fbdbf5793a7bc7b4998ecb867c8 AS deps
WORKDIR /app
COPY package.json package-lock.json .npmrc ./
RUN npm ci

# --- Development image: Vite dev server, code bind-mounted by docker compose ---
FROM deps AS dev
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# --- Static build ---
FROM deps AS build
COPY . .
# "/api/v1" when nginx proxies the API (docker-compose.prod.yml); an absolute URL otherwise.
ARG VITE_API_URL=/api/v1
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

# --- Production image: nginx serving the SPA ---
# nginx stable branch (even minor version: 1.30), with its security fixes, in the official
# variant that runs without root (user nginx, port 8080).
FROM nginxinc/nginx-unprivileged:1.30.6-alpine@sha256:f5116ed4606f3eb015dd4a8e28cb9b351476dc0ad4bc6e9f93b19cec130cdf03 AS prod
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY docker/security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
