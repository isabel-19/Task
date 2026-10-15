FROM node:24-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ENV VITE_API_URL=/api
RUN npm run build

FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 FRONTEND_DIST=/app/frontend/dist \
    APP_ENV=production DEMO_MODE=false COOKIE_SECURE=true
WORKDIR /app/backend
COPY backend/requirements.lock backend/requirements-postgres.txt backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.lock -r requirements-postgres.txt
COPY backend/app ./app
COPY backend/migrations ./migrations
COPY backend/alembic.ini ./alembic.ini
COPY database/migrations /app/database/migrations
COPY --from=frontend /build/dist /app/frontend/dist
RUN groupadd --gid 10001 roadmap && useradd --uid 10001 --gid roadmap --no-create-home roadmap \
    && mkdir -p /var/data/evidence && chown -R roadmap:roadmap /var/data
USER roadmap
EXPOSE 10000
CMD ["python", "-m", "app.serve"]
