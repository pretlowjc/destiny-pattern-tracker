# Deployment Notes

Status: **planning** — the app currently runs as Docker containers (Nginx + FastAPI) behind an ALB. This document tracks the plan and open gaps for moving to a fully managed AWS deployment (S3 + CloudFront for the frontend, Lambda + API Gateway for the backend). Nothing described as "planned" below has been implemented yet.

## Target Architecture

- **Frontend:** Angular build output served from S3, distributed via CloudFront.
- **Backend:** FastAPI wrapped with [Mangum](https://github.com/jordaneremieff/mangum), running on Lambda behind API Gateway.
- **Data:** RDS (Aurora Serverless v2) or DynamoDB, replacing the current local SQLite file.
- **Manifest cache:** moved out of process memory into S3/DynamoDB, refreshed on a schedule (EventBridge) instead of on every cold start.

## Refactor Sequence

Each phase should leave the previous phase's tests green before starting the next.

### Phase 0 — Safety net
- Add characterization tests against current behavior (`/health`, `/api/manifest-version`, `/api/patterns`) using `httpx` + `respx` to mock Bungie, before changing any backend code.
- Tag the current `develop` HEAD as a rollback point.

### Phase 1 — Extract configuration & logging
- Replace scattered `os.getenv(...)` calls with a single `pydantic-settings` `Settings` object.
- Replace `print(...)` debug statements with the `logging` module, gated by level, so nothing sensitive ships to stdout/CloudWatch by default.

### Phase 2 — Extract a service/repository layer
- Pull the pattern-merge logic out of `main.py`'s route handler into a plain-Python module so it's unit-testable without FastAPI.
- Turn `bungie_client.py`'s four standalone functions into a single `BungieClient` class, injected via `Depends`, so tests can substitute a fake.

### Phase 3 — Remove state that can't survive Lambda
- Migrate SQLite (`weapon_tracker.db`) to RDS/Aurora Serverless v2 or DynamoDB behind the Phase 2 repository interface.
- Move the in-memory `MANIFEST_CACHE` (currently loaded on FastAPI startup) to a scheduled refresh job that writes to S3/DynamoDB; request handlers read from there instead of downloading it themselves.
- Validate with a shadow-read/dual-write period comparing old vs. new storage before fully cutting over.

### Phase 4 — Wrap for Lambda, deploy in parallel
- Add `mangum`, wrap the FastAPI app, deploy behind API Gateway alongside the existing container (not replacing it yet).
- Route a small slice of traffic to the Lambda path and compare responses against the container path before trusting it.

### Phase 5 — Frontend to S3 + CloudFront
- Move the hardcoded API URL in `bungie-api.service.ts` into Angular environment files.
- CloudFront needs a second origin/behavior for `/api/*` (or keep the API on its own subdomain, relying on the existing CORS allow-list), since S3+CloudFront removes the Nginx reverse proxy.

### Phase 6 — Cutover & decommission
- Flip traffic fully to Lambda + API Gateway + S3/CloudFront; keep the container stack idle for a rollback window before decommissioning it.

## AWS Readiness Gaps

- No IaC exists yet (`deploy/` is currently empty) — no CDK/SAM/Terraform defining the S3 bucket, CloudFront distribution, Lambda function, API Gateway, or IAM roles.
- `mangum` is not in `requirements.txt`.
- Startup-time manifest download (`@app.on_event("startup")` in `main.py`) doesn't scale on Lambda — every concurrent execution environment would redownload it independently. See Phase 3.
- SQLite is a hard blocker for Lambda (ephemeral, non-shared `/tmp`, single-writer). Must migrate before any real cutover. See Phase 3.
- CI (`.github/workflows/ci.yml`) only builds/tests today — no packaging step for a Lambda artifact, no CDK/SAM deploy job, no AWS credentials wired in.
- Frontend API URL is hardcoded to `https://d2patterntracker.com/api` rather than environment-driven — fine for one prod domain, but blocks having a separate staging CloudFront distribution.
- No environment/stage separation exists (one `.env`, one CORS origin list), which makes the parallel-run/canary approach in Phase 4 harder than necessary.

## Known Security Issues (tracked, not yet remediated)

| # | Severity | Finding | Where |
|---|----------|---------|-------|
| 1 | Critical | TLS private key + cert committed to git, still recoverable from history even if deleted now | `backend/key.pem`, `backend/cert.pem` |
| 2 | High | SQLite DB file committed to git, leaking app data into history | `backend/weapon_tracker.db` |
| 3 | High | OAuth `state` param is a hardcoded literal, not per-session random — defeats CSRF protection on login | `backend/services/bungie_client.py`, `backend/main.py` |
| 4 | High | Access token passed as a URL query parameter on redirect to the frontend — leaks into browser history, access logs, Referer headers | `backend/main.py` |
| 5 | Medium | Access token stored in `localStorage` — readable by any XSS | `frontend/src/app/core/services/bungie-api.service.ts` |
| 6 | Medium | Debug `print()`s of token length/prefix and full upstream error bodies go to stdout/CloudWatch in production | `backend/services/bungie_client.py`, `backend/main.py` |
| 7 | Low-Med | `allow_methods`/`allow_headers` set to `"*"` combined with `allow_credentials=True` | `backend/main.py` |
| 8 | Low | No `.dockerignore` in either service — risks baking `venv/`, `__pycache__`, the SQLite file, and cert/key material into image layers | `backend/Dockerfile`, `frontend/Dockerfile` |
| 9 | Low | No dependency scanning in CI (no Dependabot/`pip-audit`/`npm audit`) | `.github/workflows/ci.yml` |

**Note on #1/#2:** deleting these files isn't sufficient — they remain in git history. Fixing them requires rotating the cert/key and rewriting git history (e.g. `git filter-repo`), plus adding `*.pem` and `*.db` to `.gitignore` (currently only `.env` is ignored).

## Suggestions

- Add a real backend test suite (`pytest` + `httpx` + `respx`) — there is currently no automated coverage on the OAuth flow or the pattern-merge logic.
- Add `pip-audit` and `npm audit --audit-level=high` as CI steps.
- Consider Aurora Serverless v2 over a fixed RDS instance given spiky/low traffic — it scales to near-zero cost between sessions.
