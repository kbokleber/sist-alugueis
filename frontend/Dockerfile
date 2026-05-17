FROM node:22-alpine AS builder

WORKDIR /app
ARG VITE_API_BASE_URL=/api/v1
ARG VITE_APP_NAME="Controle de Alugueis"
ARG VITE_APP_VERSION=
ARG SOURCE_COMMIT=
ARG COMMIT_SHA=
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_APP_NAME=${VITE_APP_NAME}
COPY package*.json ./
RUN npm install --include=dev
RUN apk add --no-cache git
COPY . .
RUN set -eu; \
    RESOLVED_VERSION="${VITE_APP_VERSION}"; \
    if [ -z "${RESOLVED_VERSION}" ]; then \
      RESOLVED_VERSION="${SOURCE_COMMIT}"; \
    fi; \
    if [ -z "${RESOLVED_VERSION}" ]; then \
      RESOLVED_VERSION="${COMMIT_SHA}"; \
    fi; \
    if [ -z "${RESOLVED_VERSION}" ] && [ -d .git ]; then \
      RESOLVED_VERSION="$(git rev-parse --short HEAD || true)"; \
    fi; \
    if [ -z "${RESOLVED_VERSION}" ]; then \
      RESOLVED_VERSION="dev"; \
    fi; \
    SHORT_VERSION="$(printf '%s' "${RESOLVED_VERSION}" | cut -c1-7)"; \
    echo "Building frontend with VITE_APP_VERSION=${SHORT_VERSION}"; \
    VITE_APP_VERSION="${SHORT_VERSION}" npm run build

FROM nginx:alpine
RUN apk add --no-cache gettext
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
ENTRYPOINT ["/docker-entrypoint.sh"]
