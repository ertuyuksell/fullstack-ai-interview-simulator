# Deployment Guide

## Local development (recommended first run)

```bash
cp .env.example .env
docker compose up --build
```

First boot of the AI service downloads HuggingFace models (~500 MB) into the
`hf_cache` volume. Subsequent boots are fast.

| URL                              | Service           |
| -------------------------------- | ----------------- |
| http://localhost:5173            | Frontend          |
| http://localhost:8080/api        | Backend REST      |
| ws://localhost:8080/ws/interview | Live feedback WS  |
| http://localhost:8000/docs       | AI service Swagger|

## Smoke test

```bash
# 1. Register
curl -X POST http://localhost:8080/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"a@b.com","password":"hunter22!","fullName":"A B"}'

# 2. Use the returned token
TOKEN=...
curl -X POST http://localhost:8080/api/interviews \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"role":"Backend Engineer","level":"mid"}'
```

## Production deployment

### Container registry & images

```bash
docker build -t registry.example.com/interview-frontend:1.0.0 ./frontend
docker build -t registry.example.com/interview-backend:1.0.0  ./backend
docker build -t registry.example.com/interview-ai:1.0.0       ./ai-service
docker push registry.example.com/interview-{frontend,backend,ai}:1.0.0
```

### Required environment

| Variable             | Where     | Notes                                       |
| -------------------- | --------- | ------------------------------------------- |
| `JWT_SECRET`         | backend   | 32+ random bytes, rotate on incident        |
| `SPRING_DATASOURCE_*`| backend   | Managed PostgreSQL connection details       |
| `SPRING_DATA_REDIS_*`| backend   | Managed Redis (rate limiting, sessions)     |
| `AI_SERVICE_URL`     | backend   | Internal DNS to AI service                  |
| `VITE_API_URL`       | frontend (build-time) | Public API base URL              |
| `VITE_WS_URL`        | frontend (build-time) | Public WS base URL               |

### Recommended infra

- **Postgres:** managed (RDS / Cloud SQL), nightly backups, PITR enabled.
- **Redis:** single replica is fine for the v1 feature set.
- **AI service:** behind an internal-only load balancer; scale horizontally
  by replica count. Use a node with ≥ 2 vCPU, 4 GB RAM per replica. GPU is not
  required for the bundled models — speech wav2vec2 inference is CPU-friendly.
- **Backend:** stateless, scale horizontally. Place behind an ALB/Nginx.
- **Frontend:** static `dist/` served by the nginx image, or upload to a CDN.

### Kubernetes sketch

```yaml
# Each service: Deployment + Service + Ingress (frontend + backend only).
# AI service stays cluster-internal (ClusterIP).
# Use a PVC mounted at /models for the AI replicas to share the HF cache.
```

### Hardening checklist

- [ ] HTTPS termination at the edge; HSTS on.
- [ ] Strict CORS — set `app.cors.allowed-origins` to the production frontend host only.
- [ ] Rotate `JWT_SECRET`; consider short-lived tokens + refresh tokens.
- [ ] Postgres: enforce TLS, least-privilege role for the app.
- [ ] Add a WAF/rate-limiter in front of `/api/auth/*`.
- [ ] Enable Spring Boot actuator on a separate, network-restricted port.
- [ ] Log aggregation (Loki / CloudWatch) — JSON log format on backend.
- [ ] Capture errors via Sentry (or equivalent) for backend + frontend.

### Scaling notes

- Live-feedback WebSocket connections are sticky to a single backend pod.
  Use sticky sessions at the load balancer or move to a Redis-backed pub/sub
  fan-out before scaling backend > 1 replica with active interviews.
- AI service is stateless across requests — scale freely.
- Postgres is the long-term bottleneck. Add read replicas only after observing
  contention; the current schema is small.

## Migrations

Flyway runs on backend startup. New migrations go in
`backend/src/main/resources/db/migration` as `V<n>__<name>.sql`.

## Rollback

1. Re-deploy the previous image tag for the affected service.
2. Flyway migrations are forward-only — for schema rollback, write a new
   compensating `V<n+1>__revert_*.sql` rather than running `undo`.
