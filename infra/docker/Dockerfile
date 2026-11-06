# syntax=docker/dockerfile:1
# Dockerfile dung chung cho toan bo du an. Build context la thu muc goc repo.
#   target "backend" -> API FastAPI
#   target "web"     -> React build + nginx (proxy /api toi backend)
#   target "web-dev" -> Vite dev server (hot reload, dung voi profile dev)
#   target "db-init" -> sqlcmd + bash de chay script trong database/ (schema + seed)

# ---------- Backend (FastAPI) ----------
FROM python:3.12-slim AS backend
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libltdl7 libkrb5-3 libgssapi-krb5-2 \
    && rm -rf /var/lib/apt/lists/*
COPY apps/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/backend/app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ---------- Web: build ----------
FROM node:22-alpine AS web-build
WORKDIR /app
COPY apps/web/package*.json ./
RUN npm install
COPY apps/web ./
RUN npm run build

# ---------- Web: nginx ----------
FROM nginx:alpine AS web
COPY --from=web-build /app/dist /usr/share/nginx/html
COPY infra/docker/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
# ---------- Web: Vite dev server (hot reload) ----------
FROM node:22-alpine AS web-dev
WORKDIR /app
COPY apps/web/package*.json ./
RUN npm install
EXPOSE 5173
CMD ["npm", "run", "dev"]

# ---------- DB init: chay database/init.sh ----------
FROM ubuntu:22.04 AS db-init
ENV ACCEPT_EULA=Y DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
    && curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/ubuntu/22.04/prod jammy main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update && apt-get install -y --no-install-recommends mssql-tools18 unixodbc \
    && rm -rf /var/lib/apt/lists/*
ENV PATH="${PATH}:/opt/mssql-tools18/bin"