# Setup Guide

Step-by-step instructions for setting up the NAWI Test Report Generator on your local machine.

---

## Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Python | 3.12+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |
| Git | any | `git --version` |

**Optional** (only needed for Docker setup or production):

| Tool | Purpose |
|------|---------|
| Docker & Docker Compose | Containerized setup with PostgreSQL and Redis |
| PostgreSQL 16 | Required for production; development uses SQLite by default |
| Redis 7 | Required for Celery background tasks (report generation) |

---

## Option A: Local Development (Recommended for Getting Started)

This runs the backend with SQLite (no database setup needed) and the frontend dev server.

### 1. Clone the repository

```bash
git clone https://github.com/gauravsoni02/sih-2026.git
cd sih-2026
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and set a secret key:

```
DJANGO_SECRET_KEY=any-random-string-here
DJANGO_DEBUG=True
```

Leave `DATABASE_URL` empty to use SQLite (no PostgreSQL needed for development).

### 3. Set up the backend

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```

When prompted, enter an email and password for the admin account.

Start the backend server:

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`.

### 4. Set up the frontend

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`. It automatically proxies API requests to the backend at `http://localhost:8000`.

### 5. Open the app

Go to `http://localhost:5173/login` and log in with the superuser credentials you created in step 3.

---

## Option B: Docker Setup

This runs everything in containers (PostgreSQL, Redis, and the Django backend).

### 1. Clone and configure

```bash
git clone https://github.com/gauravsoni02/sih-2026.git
cd sih-2026
cp .env.example .env
```

Edit `.env` and set:

```
DJANGO_SECRET_KEY=any-random-string-here
DATABASE_URL=postgres://nawi:password@postgres:5432/nawi_db
```

### 2. Start the containers

```bash
docker compose up -d
```

This starts three services:
- **web** (Django + Gunicorn) on port 8000
- **postgres** (PostgreSQL 16) on port 5432
- **redis** (Redis 7) on port 6379

### 3. Run migrations and create admin user

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

### 4. Set up the frontend

The frontend still runs locally (not in Docker):

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` and log in.

---

## Running Tests

### Backend tests (189 tests)

```bash
cd backend
python manage.py test
```

Run only the calculation engine tests:

```bash
python manage.py test apps.engine
```

Run tests for a specific app:

```bash
python manage.py test apps.accounts
python manage.py test apps.instruments
python manage.py test apps.testing
python manage.py test apps.reports
```

### Frontend

```bash
cd frontend
npm run lint
npm run build    # Type-check + production build
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | Yes | — | Django secret key for cryptographic signing |
| `DJANGO_DEBUG` | No | `True` | Set to `False` in production |
| `DJANGO_SETTINGS_MODULE` | No | `config.settings.development` | Use `config.settings.production` for production |
| `DJANGO_ALLOWED_HOSTS` | No | `localhost,127.0.0.1` | Comma-separated allowed hostnames |
| `DATABASE_URL` | No | — | PostgreSQL connection URL. Leave empty to use SQLite |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis connection for Celery |
| `REPORT_STORAGE_PATH` | No | `/var/nawi/reports/` | Directory for generated PDF/DOCX reports |
| `ACCESS_TOKEN_LIFETIME_MINUTES` | No | `15` | JWT access token expiry |
| `REFRESH_TOKEN_LIFETIME_DAYS` | No | `7` | JWT refresh token expiry |

---

## WeasyPrint System Dependencies

WeasyPrint (used for PDF report generation) requires system-level libraries. If you skip this, the app still works but PDF generation will fail.

**Windows:**

Install GTK3 runtime from https://github.com/nickvdyck/weasyprint-win-setup or use `msys2`:

```bash
pacman -S mingw-w64-x86_64-pango mingw-w64-x86_64-cairo
```

**macOS:**

```bash
brew install pango cairo libffi
```

**Ubuntu/Debian:**

```bash
sudo apt install python3-cffi python3-brotli libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

---

## Project Structure

```
sih-2026/
├── backend/
│   ├── config/            # Django settings, URLs, Celery
│   ├── common/            # Base models, pagination, exceptions
│   └── apps/
│       ├── accounts/      # User model, JWT auth, role permissions
│       ├── instruments/   # Instrument CRUD
│       ├── laboratory/    # Laboratory model
│       ├── testing/       # Test sessions, observations, results
│       ├── engine/        # OIML R 76 calculation engine (pure Python)
│       ├── reports/       # Report generation (PDF, DOCX)
│       └── dashboard/     # Stats and analytics endpoints
├── frontend/
│   └── src/
│       ├── api/           # Axios API client modules
│       ├── components/    # Layout, forms, charts, common
│       ├── pages/         # Route pages (Dashboard, Instruments, etc.)
│       ├── services/      # Web Serial, offline storage
│       ├── store/         # Zustand state stores
│       ├── types/         # TypeScript interfaces
│       └── utils/         # MPE lookup, validation helpers
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Troubleshooting

**`pip install` fails on `psycopg2-binary`**
You can skip PostgreSQL support for development — SQLite is used when `DATABASE_URL` is empty. If you need PostgreSQL, install the system dependency first: `sudo apt install libpq-dev` (Linux) or `brew install postgresql` (macOS).

**Frontend can't reach the backend API**
Make sure the backend is running on port 8000. The Vite dev server proxies `/api` requests to `http://localhost:8000` automatically.

**Port already in use**
Kill existing processes: `lsof -ti:8000 | xargs kill` (backend) or `lsof -ti:5173 | xargs kill` (frontend). On Windows: `netstat -ano | findstr :8000`.

**`python` command not found**
Try `python3` instead. On Windows, ensure Python is in your PATH.
