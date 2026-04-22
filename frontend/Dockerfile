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
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
