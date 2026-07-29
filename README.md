# Destiny 2 Pattern Tracker

A web application for tracking Deepsight weapon pattern progress in Destiny 2, using live data pulled from a player's account via the Bungie.net API.

## Overview

Destiny 2 players unlock weapon crafting patterns by completing "Deepsight" objectives on specific weapons. This app authenticates a player through Bungie's OAuth flow, pulls their live Triumph/Record progress, cross-references it against the Bungie game manifest to identify which records are craftable weapon patterns, and displays real-time completion progress on a dashboard.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Angular 17, TypeScript, Tailwind CSS |
| Backend | FastAPI (Python 3.11+), Uvicorn, SQLAlchemy |
| Database | SQLite (local/dev) |
| Auth | Bungie.net OAuth 2.0 |
| Containerization | Docker (multi-stage builds), Nginx (frontend reverse proxy) |
| CI | GitHub Actions |

## Project Structure

```
.
├── backend/
│   ├── main.py                  # FastAPI app, route definitions
│   ├── models.py                # Pydantic + SQLAlchemy models
│   ├── database.py              # SQLAlchemy engine/session setup
│   ├── services/
│   │   └── bungie_client.py     # Bungie.net API client (manifest, OAuth, profile)
│   ├── seed_db.py                # Dev-only DB seeding script
│   ├── update_manifest.py        # Manifest refresh utility
│   └── Dockerfile
├── frontend/
│   ├── src/app/
│   │   ├── core/services/        # BungieApiService (HTTP client wrapper)
│   │   └── features/
│   │       ├── login/            # Bungie OAuth login screen
│   │       ├── dashboard/        # Live pattern progress view
│   │       └── settings/
│   ├── nginx.conf                 # Reverse-proxies /api to the backend
│   └── Dockerfile
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## Prerequisites

- Python 3.11+
- Node.js 20+ and npm
- A [Bungie.net application](https://www.bungie.net/en/Application) with a registered OAuth Client ID/Secret and an API key

## Local Setup

### 1. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:

```
BUNGIE_API_KEY=your_api_key
BUNGIE_CLIENT_ID=your_client_id
BUNGIE_CLIENT_SECRET=your_client_secret
```

Run the API:

```bash
uvicorn main:app --reload --port 8000
```

The API serves on `http://localhost:8000`. On startup it downloads the Bungie manifest's Record definitions into memory (used to identify which Triumphs are weapon patterns).

### 2. Frontend

```bash
cd frontend
npm install
npm start
```

Serves on `http://localhost:4200`.

### 3. Docker (both services)

```bash
docker-compose up --build
```

Backend on `:8000`, frontend (via Nginx) on `:4200`, with `/api/*` proxied to the backend container.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/api/manifest-version` | Current Bungie manifest version |
| GET | `/api/auth/login` | Redirects to Bungie's OAuth authorize page |
| GET | `/api/auth/callback` | OAuth callback; exchanges code for token, redirects to frontend |
| GET | `/api/auth/profile` | Returns the authenticated user's Destiny membership info |
| GET | `/api/patterns` | Returns the authenticated user's live weapon pattern progress |

`/api/patterns` and `/api/auth/profile` require an `Authorization: Bearer <token>` header.

## Deployment

The frontend is built to static assets and served by Nginx; the backend runs as a standalone container behind a reverse proxy. See [docker-compose.yml](docker-compose.yml) and each service's `Dockerfile` for the current container setup. A move to a fully managed AWS deployment (S3 + CloudFront for the frontend, Lambda + API Gateway for the backend) is planned but not yet implemented — see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the migration plan, known security issues, and open gaps before treating that path as production-ready.

## Known Limitations

- The backend currently uses a local SQLite file and an in-memory manifest cache, which limits it to single-instance deployments.
- No automated backend test suite exists yet.

## License

MIT — see [LICENSE](LICENSE).
