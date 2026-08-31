# NAWI Test Report Generator

A web application for generating test reports for **Non-Automatic Weighing Instruments (NAWIs)** per [OIML Recommendation R 76-1:2006](https://www.oiml.org/en/files/pdf_r/r076-1-e06.pdf).

Built for government metrology laboratories in India under the Legal Metrology Act, 2009 to evaluate and certify weighing instruments — electronic scales, platform scales, and weighbridges.

## What it does

- **Register instruments** — store manufacturer, model, serial number, accuracy class (I–IIII), capacities, scale intervals (d and e), multi-interval configurations
- **Run test sessions** — enter observations for 13+ test types (weighing performance, eccentricity, repeatability, discrimination, sensitivity, tare, creep, temperature, tilt, power supply, durability, span stability, zero tracking)
- **Compute errors automatically** — OIML R 76 MPE lookup for all 4 accuracy classes, both initial and subsequent verification, multi-interval support
- **Live error feedback** — client-side error calculation on every keystroke with pass/fail determination and an interactive error-vs-load chart with MPE envelope
- **Generate PDF/DOCX reports** — standardized test reports with cover page, instrument details, environmental conditions, measurement tables, compliance summary, and signatory block
- **In-browser report preview** — print-ready formal report layout with Government of India header
- **Dashboard analytics** — metric cards with trends, testing trend charts (pass/fail stacked bars), pass/fail pie chart, measurement error profile
- **Activity log** — audit trail of all changes with search and severity filtering
- **Settings** — profile, laboratory, preferences, report configuration, connections, about

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, Django 5.x, Django REST Framework 3.15 |
| Frontend | React 18, TypeScript 5.5, Vite, Ant Design 5.x, Zustand, React Query |
| Charts | Recharts |
| Database | PostgreSQL 16 (SQLite for development) |
| Task queue | Celery + Redis |
| Reports | WeasyPrint / ReportLab (PDF), python-docx (DOCX) |
| Auth | djangorestframework-simplejwt |
| Audit | django-auditlog |
| Containerization | Docker, Docker Compose |

## Quick start

### Backend

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server runs at `http://localhost:5173` and proxies API requests to `http://localhost:8000`.

### Docker

```bash
docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

## Project structure

```
├── backend/
│   ├── config/            # Django settings, URLs, WSGI, Celery
│   ├── common/            # Base models, pagination, exceptions
│   └── apps/
│       ├── accounts/      # User model, JWT auth, permissions
│       ├── instruments/   # Instrument CRUD
│       ├── laboratory/    # Laboratory model
│       ├── testing/       # Test sessions, observations, results
│       ├── engine/        # Pure R 76 calculation engine (no views)
│       ├── reports/       # Report generation (PDF, DOCX)
│       └── dashboard/     # Stats, charts, audit log endpoints
├── frontend/
│   └── src/
│       ├── api/           # Axios API modules
│       ├── components/    # Layout, forms, charts, common
│       ├── pages/         # Route pages
│       ├── services/      # Web Serial, offline storage
│       ├── store/         # Zustand stores
│       ├── types/         # TypeScript interfaces
│       └── utils/         # MPE lookup, validation, demo data
├── CLAUDE.md              # Project spec and domain knowledge
├── docker-compose.yml
└── .env.example
```

## Domain knowledge

The calculation engine implements OIML R 76-1:2006 exactly:

- **MPE Table 6** — boundary-correct lookup (`≤` on upper bounds) for all 4 accuracy classes
- **Multi-interval instruments** — partial range detection, per-range e values
- **d vs e distinction** — discrimination uses d (actual scale interval), MPE uses e (verification scale interval)
- **All arithmetic in `Decimal`** — no floating-point errors at MPE boundaries
- **189 backend tests** covering MPE boundaries, multi-interval edge cases, error computation, eccentricity, repeatability, discrimination, creep, compliance, and API permissions

## Environment variables

Copy `.env.example` to `.env` and fill in:

```
DJANGO_SECRET_KEY=
DJANGO_DEBUG=True
DATABASE_URL=postgres://nawi:password@localhost:5432/nawi_db
REDIS_URL=redis://localhost:6379/0
```

## License

[MIT](LICENSE)
