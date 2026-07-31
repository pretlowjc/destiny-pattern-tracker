# Destiny 2 Pattern Tracker

[![CI](https://github.com/pretlowjc/destiny-pattern-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/pretlowjc/destiny-pattern-tracker/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Track your Deepsight weapon pattern progress in Destiny 2, pulled live from your Bungie.net account.

<!-- TODO: replace with a real screenshot or GIF of the dashboard -->
<!-- ![Dashboard](docs/images/dashboard.png) -->

## The problem

Destiny 2 players unlock weapon crafting patterns by completing "Deepsight" objectives, but the game scatters that progress across hundreds of individual Triumph records with no consolidated view. Players resort to spreadsheets or manual menu-diving to answer a simple question: *which patterns am I close to finishing?*

This app answers that in one screen.

## How it works

1. Authenticates the player through Bungie's OAuth 2.0 flow
2. Fetches their live Triumph/Record progress from the Bungie.net API
3. Cross-references those records against the Bungie game manifest to identify which ones are craftable weapon patterns
4. Renders completion progress on a dashboard

The manifest cross-reference is the non-obvious part — Bungie's API returns record progress as opaque hashes, so the app loads the manifest's Record definitions on startup and resolves them in memory to determine which records represent patterns.

## Tech stack

| Layer            | Technology                                                  |
| ---------------- | ----------------------------------------------------------- |
| Frontend         | Angular 17, TypeScript, Tailwind CSS                        |
| Backend          | FastAPI (Python 3.11+), Uvicorn, SQLAlchemy                 |
| Database         | SQLite (local/dev)                                          |
| Auth             | Bungie.net OAuth 2.0                                        |
| Containerization | Docker (multi-stage builds), Nginx (frontend reverse proxy) |
| CI               | GitHub Actions                                              |

## API

| Method | Path                    | Description                                                     |
| ------ | ----------------------- | --------------------------------------------------------------- |
| GET    | `/health`               | Liveness check                                                  |
| GET    | `/api/manifest-version` | Current Bungie manifest version                                 |
| GET    | `/api/auth/login`       | Redirects to Bungie's OAuth authorize page                      |
| GET    | `/api/auth/callback`    | OAuth callback; exchanges code for token, redirects to frontend |
| GET    | `/api/auth/profile`     | Returns the authenticated user's Destiny membership info        |
| GET    | `/api/patterns`         | Returns the authenticated user's live weapon pattern progress   |

`/api/patterns` and `/api/auth/profile` require an `Authorization: Bearer <token>` header.

## Project structure

```
.
├── backend/
│   ├── main.py                   # FastAPI app, route definitions
│   ├── models.py                 # Pydantic + SQLAlchemy models
│   ├── database.py               # SQLAlchemy engine/session setup
│   ├── services/
│   │   └── bungie_client.py      # Bungie.net API client (manifest, OAuth, profile)
│   ├── seed_db.py                # Dev-only DB seeding script
│   ├── update_manifest.py        # Manifest refresh utility
│   └── Dockerfile
├── frontend/
│   ├── src/app/
│   │   ├── core/services/        # BungieApiService (typed HTTP client wrapper)
│   │   └── features/
│   │       ├── login/            # Bungie OAuth login screen
│   │       ├── dashboard/        # Live pattern progress view
│   │       └── settings/
│   ├── nginx.conf                # Reverse-proxies /api to the backend
│   └── Dockerfile
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## Running it locally

### Prerequisites

- Python 3.11+
- Node.js 20+ and npm
- A [Bungie.net application](https://www.bungie.net/en/Application) with a registered OAuth Client ID/Secret and an API key

### Quick start (Docker)

```bash
# Create backend/.env first (see below), then:
docker-compose up --build
```

Backend on `:8000`, frontend on `:4200`, with `/api/*` proxied to the backend container.

### Manual setup

**Backend**

```bash
cd backend
python -m venv venv

# macOS / Linux
source venv/bin/activate
# Windows
venv\Scripts\activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Create `backend/.env`:

```
BUNGIE_API_KEY=your_api_key
BUNGIE_CLIENT_ID=your_client_id
BUNGIE_CLIENT_SECRET=your_client_secret
```

On startup the API downloads the Bungie manifest's Record definitions into memory.

**Frontend**

```bash
cd frontend
npm install
npm start
```

Serves on `http://localhost:4200`.

## Deployment status

The application runs as two containers: an Nginx-served Angular static build and a FastAPI backend behind a reverse proxy. See [`docker-compose.yml`](docker-compose.yml) and each service's `Dockerfile`.

A migration to a fully managed AWS deployment — S3 + CloudFront for the frontend, Lambda + API Gateway for the backend — is scoped but not yet implemented. The migration plan and the gaps that need closing first are documented in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

Known gaps before this is production-ready:

- Secrets are loaded from a local `.env` file and would need to move to AWS Secrets Manager or Parameter Store
- OAuth tokens are handled client-side; a production deployment needs server-side session storage
- SQLite and the in-memory manifest cache limit the backend to a single instance; a managed database and shared cache are required to scale horizontally
- No automated backend test suite yet

## Roadmap

- [ ] pytest suite covering the Bungie client and API routes
- [ ] Serverless migration (S3/CloudFront + Lambda/API Gateway)
- [ ] Move manifest cache out of process
- [ ] Server-side session handling for OAuth tokens
- [ ] Live public deployment

## License

MIT — see [LICENSE](LICENSE).
