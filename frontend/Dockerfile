FROM node:22-alpine AS builder

WORKDIR /app
ARG VITE_API_BASE_URL=/api/v1
ARG VITE_APP_NAME="Controle de Alugueis"
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_APP_NAME=${VITE_APP_NAME}
COPY package*.json ./
RUN npm install --include=dev
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
