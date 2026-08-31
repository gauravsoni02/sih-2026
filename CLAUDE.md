# CLAUDE.md — NAWI Test Report Generator

## Project overview

Software application for generating test reports for Non-Automatic Weighing Instruments (NAWIs) per OIML Recommendation R-76. Used by government metrology labs in India under the Legal Metrology Act, 2009 to evaluate and certify weighing instruments (electronic scales, platform scales, weighbridges).

The system replaces manual paper-based report generation. Lab technicians enter test observations, the system computes errors and compliance automatically, and generates standardized PDF/DOCX reports.

---

## Development phases

Build in this exact order. Do not skip ahead. Each phase must be working and tested before starting the next.

### PHASE 1 — Foundation (scaffold, database, config)

**Goal**: A running Django project with PostgreSQL, base models, and Docker setup. No UI.

**Build**:
- Project scaffold matching the directory structure below
- Django settings split: `base.py`, `development.py`, `production.py`
- `common/models.py` with `TimeStampedModel` (provides `created_at`, `updated_at`, `is_deleted` soft-delete)
- PostgreSQL database with initial migrations
- Docker Compose: `web`, `postgres`, `redis` services
- `.env.example` with all env vars documented
- `config/celery.py` wired up (workers come later)

**Test**: `docker compose up` starts cleanly, `python manage.py migrate` runs, `python manage.py createsuperuser` works.

**Files to create**:
```
backend/config/settings/base.py
backend/config/settings/development.py
backend/config/settings/production.py
backend/config/urls.py
backend/config/celery.py
backend/config/wsgi.py
backend/common/models.py
backend/common/pagination.py
backend/common/exceptions.py
backend/manage.py
backend/requirements.txt
docker-compose.yml
.env.example
```

---

### PHASE 2 — Calculation engine (pure Python, no views)

**Goal**: The complete OIML R-76 calculation engine with exhaustive tests. This is the most important code in the entire project — every number on every report comes from here.

**Build**:
- `apps/engine/mpe.py` — MPE lookup for all 4 accuracy classes, both verification types
- `apps/engine/calculations.py` — error computation, eccentricity, repeatability, discrimination, sensitivity
- `apps/engine/compliance.py` — pass/fail determination, overall verdict
- `apps/engine/validators.py` — input validation (range checks, consistency checks)
- `apps/engine/constants.py` — accuracy class enums, test type enums, unit enums

**Test** (write these FIRST, then implement to pass them):

MPE lookup tests:
1. MPE for all 4 classes at every boundary point (exactly 500e for Class III → 0.5e, not 1.0e)
2. MPE at boundary ± 1 (499e → 0.5e, 501e → 1.0e for Class III)
3. MPE at zero load → 0.5e
4. Initial vs subsequent verification (subsequent = 2× initial MPE)
5. MPE for Class I at 200,001e (above max listed range — should raise error or use 1.0e)

Multi-interval tests:
6. Multi-interval Class III worked example from R-76 Section 3.3 — reproduce EXACTLY:
   - m=500g → MPE=0.5g, m=501g → MPE=1.0g (range 1, e1=1g)
   - m=2000g → MPE=1.0g, m=2001g → MPE=2.0g (transition to range 2, e2=2g)
   - m=4000g → MPE=2.0g, m=4001g → MPE=3.0g (still range 2)
   - m=5000g → MPE=3.0g, m=5001g → MPE=10.0g (transition to range 3, e3=10g)
7. Multi-interval edge: load exactly at partial range boundary (e.g., exactly Max1)

Error computation tests:
8. Error with positive, negative, and zero corrections
9. Error = indication - (load + correction), verify sign convention
10. Compliance at exactly MPE → PASS
11. Compliance at MPE + 0.001 (smallest Decimal increment) → FAIL

Eccentricity tests:
12. Eccentricity test load calculation: 1/3 × (Max + T+) with T+ > 0
13. Eccentricity test load calculation: 1/3 × Max when T+ = 0
14. Eccentricity with identical readings → 0 error, PASS
15. Eccentricity with difference > MPE → FAIL
16. Eccentricity with difference exactly at MPE → PASS

Repeatability tests:
17. Repeatability range at boundary (range = |MPE|) → PASS
18. Repeatability range exceeding |MPE| by smallest increment → FAIL

Discrimination tests:
19. Discrimination with exactly 1.4d added, indication changes → PASS
20. Discrimination with 1.4d added, no change → FAIL
21. Discrimination skipped when d < 5mg (should return NOT_APPLICABLE)
22. Discrimination uses d (not e) — test with d ≠ e instrument

Creep tests:
23. Creep: 0min-to-30min diff ≤ 0.5e AND 15min-to-30min diff ≤ 0.2e → PASS
24. Creep: 0-30min diff = 0.6e → FAIL
25. Creep: 0-30min diff = 0.4e but 15-30min diff = 0.3e → FAIL (both must pass)

Validation tests:
26. Test load below Min → warning/error
27. All 4 accuracy classes end-to-end with realistic complete test session data
28. Temperature zero-drift: verify 1e/1°C for Class I, 1e/5°C for others

**No frontend, no API, no views.** This is a standalone Python module. Run with `python manage.py test apps.engine`.

**Files to create**:
```
backend/apps/engine/__init__.py
backend/apps/engine/constants.py
backend/apps/engine/mpe.py
backend/apps/engine/calculations.py
backend/apps/engine/compliance.py
backend/apps/engine/validators.py
backend/apps/engine/tests/__init__.py
backend/apps/engine/tests/test_mpe.py
backend/apps/engine/tests/test_calculations.py
backend/apps/engine/tests/test_compliance.py
backend/apps/engine/tests/test_validators.py
```

---

### PHASE 3 — Backend API (models, serializers, views)

**Goal**: Complete REST API for all entities. Testable with curl or Postman. No frontend yet.

**Build in this order**:

**3a — Auth & users**:
- `User` model extending `AbstractUser` with `role` field (admin, lab_manager, engineer, viewer)
- `Laboratory` model (name, address, accreditation_number, contact)
- User belongs to a laboratory
- JWT login/refresh/logout endpoints
- Role-based permission classes in `accounts/permissions.py`

**3b — Instruments**:
- `Instrument` model: manufacturer, model, serial_number, accuracy_class, max_capacity, min_capacity, verification_interval_e, num_scale_intervals_n, tare_device_type, multi_interval_config (JSONB), unit, status
- CRUD API with filtering by accuracy_class, manufacturer, status
- Serial number unique per manufacturer (compound unique constraint)

**3c — Test sessions & observations**:
- `TestSession` model: instrument (FK), laboratory (FK), engineer (FK), session_date, temperature_start, temperature_end, humidity, barometric_pressure, status (draft/in_progress/completed)
- `TestObservation` model: session (FK), test_type (enum), test_point_load, indicated_value, reference_value, correction, position (for eccentricity), trial_number, all as Decimal
- `TestResult` model: session (FK), test_type, computed_error, mpe_applicable, compliance_status, remarks
- Bulk observation POST endpoint (array of observations, atomic save)
- Calculate endpoint: `POST /api/sessions/{id}/calculate/` — runs engine, saves results

**3d — Reports (model only, generation comes in Phase 5)**:
- `Report` model: report_number, session (FK), generated_by (FK), approved_by (FK), overall_verdict, pdf_path, docx_path, version, status (draft/approved)
- Auto-generated report number: `NAWI/{lab_code}/{YYYY}/{NNNN}`

**Test**: Full API test suite — CRUD operations, permission checks (engineer can't approve, viewer can't write), bulk observation entry, calculation trigger.

**Files to create**:
```
backend/apps/accounts/models.py
backend/apps/accounts/serializers.py
backend/apps/accounts/views.py
backend/apps/accounts/permissions.py
backend/apps/accounts/urls.py
backend/apps/accounts/tests/

backend/apps/instruments/models.py
backend/apps/instruments/serializers.py
backend/apps/instruments/views.py
backend/apps/instruments/urls.py
backend/apps/instruments/tests/

backend/apps/laboratory/models.py
backend/apps/laboratory/serializers.py
backend/apps/laboratory/views.py
backend/apps/laboratory/urls.py
backend/apps/laboratory/tests/

backend/apps/testing/models.py
backend/apps/testing/serializers.py
backend/apps/testing/views.py
backend/apps/testing/urls.py
backend/apps/testing/tests/

backend/apps/reports/models.py
backend/apps/reports/serializers.py
backend/apps/reports/views.py
backend/apps/reports/urls.py
```

---

### PHASE 4 — Frontend (minimalist UI)

**Goal**: Complete working frontend. A lab technician can log in, register an instrument, run a test session, enter observations, see computed results.

**Read the UI design rules below carefully before writing any component.**

**Build in this order**:

**4a — Shell & auth**:
- Login page (email + password, nothing else)
- App shell: thin left sidebar with icon nav, content area
- Sidebar items: Dashboard, Instruments, Test Sessions, Reports
- Logout in sidebar footer

**4b — Instruments**:
- Instrument list page — a plain table with columns: serial, manufacturer, model, class, Max, status
- Instrument detail page — all specs in a simple two-column key-value layout
- "Register instrument" page — single-column form, grouped into sections with thin gray dividers

**4c — Test sessions (the main workflow)**:
- "New test session" — step 1: select instrument (searchable dropdown), step 2: enter environmental conditions (temperature, humidity, pressure), creates session
- Test session detail page — shows instrument info at top, then a tab bar for each test type
- Each test tab contains a data entry table (rows = test points, columns = reference load, indicated value, correction)
- "Calculate" button runs the engine and shows results inline: error, MPE, pass/fail per row
- Overall session verdict shown at the top after calculation

**4d — Test entry forms** (one component per test type):
- `WeighingPerformanceForm` — table with rows for each test load (increasing then decreasing)
- `EccentricityForm` — visual position selector (center + 4 corners) + reading per position
- `RepeatabilityForm` — simple repeated readings table (configurable number of trials)
- `DiscriminationForm` — load, reading before, reading after adding 1.4d
- `SensitivityForm` — at zero and max: reading, reading after adding 1d
- `TareForm`, `TemperatureForm`, `TiltForm`, `PowerSupplyForm`, `DurabilityForm`, `SpanStabilityForm`, `ZeroTrackingForm`, `TimeDependenceForm`
- All forms: auto-save drafts, client-side validation, clear error states

**Files to create**:
```
frontend/package.json
frontend/tsconfig.json
frontend/vite.config.ts
frontend/index.html
frontend/src/main.tsx
frontend/src/App.tsx
frontend/src/api/client.ts
frontend/src/api/auth.ts
frontend/src/api/instruments.ts
frontend/src/api/sessions.ts
frontend/src/api/reports.ts
frontend/src/store/authStore.ts
frontend/src/store/uiStore.ts
frontend/src/pages/Login.tsx
frontend/src/pages/Dashboard.tsx
frontend/src/pages/instruments/InstrumentList.tsx
frontend/src/pages/instruments/InstrumentDetail.tsx
frontend/src/pages/instruments/InstrumentCreate.tsx
frontend/src/pages/testing/SessionList.tsx
frontend/src/pages/testing/SessionDetail.tsx
frontend/src/pages/testing/SessionCreate.tsx
frontend/src/pages/reports/ReportList.tsx
frontend/src/pages/reports/ReportDetail.tsx
frontend/src/components/layout/AppShell.tsx
frontend/src/components/layout/Sidebar.tsx
frontend/src/components/layout/Header.tsx
frontend/src/components/forms/WeighingPerformanceForm.tsx
frontend/src/components/forms/EccentricityForm.tsx
frontend/src/components/forms/RepeatabilityForm.tsx
frontend/src/components/forms/DiscriminationForm.tsx
frontend/src/components/forms/SensitivityForm.tsx
frontend/src/components/forms/TareForm.tsx
frontend/src/components/forms/TemperatureForm.tsx
frontend/src/components/forms/TiltForm.tsx
frontend/src/components/forms/PowerSupplyForm.tsx
frontend/src/components/forms/DurabilityForm.tsx
frontend/src/components/forms/SpanStabilityForm.tsx
frontend/src/components/forms/ZeroTrackingForm.tsx
frontend/src/components/forms/TimeDependenceForm.tsx
frontend/src/components/common/StatusTag.tsx
frontend/src/components/common/PageHeader.tsx
frontend/src/components/common/EmptyState.tsx
frontend/src/types/instrument.ts
frontend/src/types/session.ts
frontend/src/types/report.ts
frontend/src/hooks/useAuth.ts
frontend/src/utils/mpe.ts
frontend/src/utils/validation.ts
```

---

### PHASE 5 — Report generation

**Goal**: Generate standardized PDF and DOCX test reports from completed sessions.

**Build**:
- `reports/generators/pdf.py` — ReportLab + WeasyPrint PDF generation
  - Cover page: lab name, accreditation, report number, date, instrument ID
  - Instrument details section
  - Environmental conditions section
  - One table per test type: test point, reference, indicated, error, MPE, status
  - Compliance summary: list of all tests with pass/fail
  - Overall verdict: CONFORMS / DOES NOT CONFORM
  - Signatory block: tested by, checked by, approved by
- `reports/generators/docx.py` — python-docx Word generation (same layout as PDF)
- `reports/tasks.py` — Celery task for async generation
- Report versioning: regenerating creates version 2, keeps version 1
- Report approval workflow: engineer generates → lab_manager approves
- Download endpoints: `/api/reports/{id}/download/pdf/` and `/download/docx/`
- Frontend: "Generate Report" button on completed sessions, download buttons on report detail page
- Report list page with status filtering (draft/approved)

**Test**: Generate report for a Class III instrument with all tests, verify PDF opens correctly, verify DOCX opens correctly, verify report number auto-increments.

**Files to create**:
```
backend/apps/reports/generators/__init__.py
backend/apps/reports/generators/pdf.py
backend/apps/reports/generators/docx.py
backend/apps/reports/templates/report_base.html
backend/apps/reports/tasks.py
backend/apps/reports/tests/test_generators.py
```

---

### PHASE 6 — Dashboard, search & hardening

**Goal**: Analytics dashboard, full-text search, audit trail, production readiness.

**Build**:
- Dashboard page with 4 stat cards: total instruments, sessions this month, reports generated, pass rate
- Simple bar chart: tests per month (last 12 months)
- Table: recent sessions with status
- Full-text search across reports (PostgreSQL `SearchVector`)
- Report search page with filters: date range, accuracy class, manufacturer, verdict
- `django-auditlog` integration for all model changes
- Rate limiting on auth endpoints
- CORS configuration
- Nginx config for production
- Gunicorn config
- Production Docker Compose with SSL

**Test**: Search returns relevant results, dashboard numbers match database, audit log captures all changes.

---

## Tech stack

- **Backend**: Python 3.12, Django 5.x, Django REST Framework 3.15
- **Frontend**: React 18 + TypeScript, Ant Design 5.x, Vite, Zustand, React Query
- **Database**: PostgreSQL 16
- **Task queue**: Celery + Redis
- **Report generation**: ReportLab, WeasyPrint (PDF), python-docx (DOCX)
- **Auth**: djangorestframework-simplejwt
- **Containerization**: Docker, Docker Compose
- **Web server**: Nginx + Gunicorn

---

## UI design rules

This is a tool for government lab technicians. They care about entering data fast and reading results clearly. The UI must be invisible — it should feel like a well-organized paper form, not a startup product.

### Philosophy
- Every screen has ONE job. No multi-purpose pages.
- If a technician can't figure out what to do in 3 seconds, the page is wrong.
- Data density over decoration. Show more information, fewer visual effects.
- The system is the background. The data is the foreground.

### Color
- **Background**: pure white `#ffffff`
- **Surface/cards**: no cards. Use whitespace and thin dividers (`#e8e8e8`) to separate sections.
- **Text**: `#1a1a1a` for primary, `#666666` for secondary, `#999999` for hints
- **Pass**: `#389e0d` (muted green) — text only, no background badge
- **Fail**: `#cf1322` (muted red) — text only, no background badge
- **Primary action**: `#1677ff` (Ant Design default blue) — buttons and links only
- **No other colors.** No gradients, no colored backgrounds on sections, no accent bars.

### Typography
- Use Ant Design's default system font stack. Do not add custom fonts.
- Page title: 20px, weight 600
- Section heading: 16px, weight 600
- Body/table text: 14px, weight 400
- Help text: 12px, weight 400, color `#999999`
- **No all-caps anywhere.** No letter-spacing on headings.

### Layout
- Max content width: 960px, centered. Test entry forms can go to 1100px.
- Sidebar: 56px wide (collapsed, icon-only by default). Expandable to 200px on hover.
- Page padding: 24px horizontal, 16px vertical.
- Section spacing: 32px between major sections. 16px between related fields.
- **No cards with shadows.** Use flat layout with thin bottom borders between items.

### Tables (the primary UI pattern)
- Tables are the main way to display data. Use Ant Design `<Table>` with:
  - Compact size (`size="small"`)
  - No outer border, thin row dividers only
  - Fixed header on scroll
  - Right-align all numeric columns
  - Monospace font (`font-variant-numeric: tabular-nums`) for numbers in tables
  - Alternating row backgrounds: white and `#fafafa`
  - Sort indicators on column headers where applicable
  - No colored row backgrounds for pass/fail — use text color only

### Forms
- Single-column layout for instrument registration and session creation.
- Labels above inputs, not beside them.
- Required field indicator: small red asterisk, nothing more.
- Group related fields with a plain text section heading and a thin divider above.
- Validation errors: red text below the field, 12px. No icons, no toasts.
- Submit button at bottom-right, primary blue. One button per form — no "Save Draft" vs "Submit" split until Phase 5.
- **No wizards or multi-step flows with fancy progress bars.** Use simple tabs or a single scrollable form.

### Test data entry tables (the most important UI)
- These are editable tables. Rows = test points, columns = fields.
- Use Ant Design's `<Table>` with inline `<InputNumber>` cells.
- Tab key moves between cells (left to right, then next row).
- After calculation, computed columns (error, MPE, status) appear as read-only colored text.
- "Add row" link at the bottom of the table, not a floating button.
- "Calculate" button: plain primary button below the table, not in a toolbar.
- **No drag-and-drop, no reordering, no inline editing modals.** Direct cell input only.

### Status display
- Session status: plain text tag — "Draft" (gray text), "In Progress" (blue text), "Completed" (green text)
- Test result: "Pass" in `#389e0d`, "Fail" in `#cf1322`, plain text, no background
- Overall verdict: a single line at the top of the session page — "CONFORMS" or "DOES NOT CONFORM" in the appropriate color, 16px weight 600

### Things to NEVER add
- Animated transitions between pages
- Loading skeletons (use a simple centered spinner)
- Toast notifications (use inline success/error messages)
- Floating action buttons
- Hero sections or banners
- Onboarding tours or tooltips
- Empty state illustrations (use plain text: "No instruments registered yet")
- Breadcrumbs (sidebar + page title is enough)
- Hover cards or popovers for data preview
- Dark mode (government labs use standard monitors)

### Responsive behavior
- Desktop-first. Minimum supported width: 1024px.
- Tables scroll horizontally on smaller screens rather than reflowing.
- Sidebar collapses to icons below 1200px.
- No mobile layout needed — this is a lab desktop application.

---

## Project structure

```
nawi/
├── CLAUDE.md
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   ├── celery.py
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── accounts/
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── permissions.py
│   │   │   └── tests/
│   │   ├── instruments/
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   └── tests/
│   │   ├── laboratory/
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   └── tests/
│   │   ├── testing/
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   └── tests/
│   │   ├── engine/                # NO views — pure calculation logic
│   │   │   ├── constants.py
│   │   │   ├── mpe.py
│   │   │   ├── calculations.py
│   │   │   ├── compliance.py
│   │   │   ├── validators.py
│   │   │   └── tests/
│   │   ├── reports/
│   │   │   ├── models.py
│   │   │   ├── generators/
│   │   │   │   ├── pdf.py
│   │   │   │   └── docx.py
│   │   │   ├── templates/
│   │   │   ├── tasks.py
│   │   │   ├── views.py
│   │   │   └── tests/
│   │   └── dashboard/
│   │       ├── views.py
│   │       └── tests/
│   └── common/
│       ├── models.py
│       ├── pagination.py
│       └── exceptions.py
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/
│       │   ├── client.ts
│       │   ├── auth.ts
│       │   ├── instruments.ts
│       │   ├── sessions.ts
│       │   └── reports.ts
│       ├── store/
│       │   ├── authStore.ts
│       │   └── uiStore.ts
│       ├── pages/
│       │   ├── Login.tsx
│       │   ├── Dashboard.tsx
│       │   ├── instruments/
│       │   ├── testing/
│       │   └── reports/
│       ├── components/
│       │   ├── layout/
│       │   ├── forms/
│       │   └── common/
│       ├── hooks/
│       ├── types/
│       └── utils/
└── docs/
```

---

## Commands

```bash
# Backend
cd backend
pip install -r requirements.txt --break-system-packages
python manage.py migrate
python manage.py runserver
python manage.py test                    # all tests
python manage.py test apps.engine        # engine tests only
python manage.py createsuperuser

# Frontend
cd frontend
npm install
npm run dev                              # dev server :5173
npm run build
npm run lint

# Docker
docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser

# Celery (Phase 5+)
celery -A config worker -l info
celery -A config beat -l info
```

---

## Coding conventions

### Python / Django
- Type hints on all function signatures
- Models inherit from `common.models.TimeStampedModel`
- All business logic in `apps/engine/` — views call engine functions, never compute themselves
- `Decimal` for ALL measurement values, never `float`
- Enums use Django `TextChoices`: `AccuracyClass`, `TestType`, `SessionStatus`, `ReportStatus`
- Always `.select_related()` / `.prefetch_related()` on querysets
- No `print()` — use `logging.getLogger(__name__)`
- Serializers: `ModelSerializer` with custom `validate_*` for field-level checks
- Views: `ModelViewSet` for CRUD, `@action` for custom endpoints
- Permissions: each app's `permissions.py`, not inline

### TypeScript / React
- Functional components only
- API data via React Query hooks in `src/api/`
- UI state only in Zustand (sidebar, tabs). Server data never in Zustand.
- Forms: Ant Design `<Form>` with field validation
- `interface` for data shapes, `type` only for unions
- PascalCase for components, camelCase for hooks and utils
- No `any` — use `unknown` + type guards

### Git
- Branches: `phase-1/scaffold`, `phase-2/engine`, `phase-3/api`, etc.
- Commits: imperative mood — "Add eccentricity form", "Fix MPE boundary for Class II"
- Tag each phase completion: `v0.1.0` (Phase 1), `v0.2.0` (Phase 2), etc.

---

## Domain knowledge — OIML R 76-1:2006

Source: https://www.oiml.org/en/files/pdf_r/r076-1-e06.pdf
This section is derived directly from the standard. Get any of this wrong and reports are invalid.

### Key distinction: d vs e

Two different scale intervals exist. Confusing them is a common bug.

- `d` = actual scale interval — the smallest increment the display shows
- `e` = verification scale interval — used for classification and error limits

For most instruments (Class III, IIII without auxiliary devices): d = e.
For Class I/II with auxiliary indicating devices: d < e ≤ 10d.
The MPE table always uses `e`, never `d`. The discrimination test uses `d`.

### Accuracy classes (Table 3 of R-76)

| Class | Name | e range | n_min | n_max | Min |
|-------|------|---------|-------|-------|-----|
| I | Special | 0.001g ≤ e | 50,000 | — | 100e |
| II | High | 0.001g ≤ e ≤ 0.05g | 100 | 100,000 | 20e |
| II | High | 0.1g ≤ e | 5,000 | 100,000 | 50e |
| III | Medium | 0.1g ≤ e ≤ 2g | 100 | 10,000 | 20e |
| III | Medium | 5g ≤ e | 500 | 10,000 | 20e |
| IIII | Ordinary | 5g ≤ e | 100 | 1,000 | 10e |

Where: e = verification scale interval, n = Max/e, Min = minimum capacity.
Min is reduced to 5e for grading instruments (postal scales, waste weighers).

**The Min value matters**: the system must validate that test loads are ≥ Min. Readings below Min are unreliable and should be flagged.

### Units of measurement (Section 2.1)

Permitted units: kg, g, mg, tonne (t), metric carat (ct, 1 ct = 0.2g).
Store the unit with every instrument. All calculations use the instrument's declared unit.

### Maximum Permissible Error (MPE) — Table 6

This is the most critical lookup in the entire system. Load `m` is expressed in multiples of `e`.

```python
# TABLE 6 — MPE ON INITIAL VERIFICATION
# Note: boundary uses ≤ on upper end. Load AT the boundary falls in the LOWER range.

MPE_TABLE = {
    'I': [
        (0,      50_000,  Decimal('0.5')),   # 0 ≤ m ≤ 50000e  → ±0.5e
        (50_000, 200_000, Decimal('1.0')),   # 50000 < m ≤ 200000e → ±1.0e
        # Class I has no 1.5e range (n_max is unlimited)
    ],
    'II': [
        (0,      5_000,   Decimal('0.5')),   # 0 ≤ m ≤ 5000e   → ±0.5e
        (5_000,  20_000,  Decimal('1.0')),   # 5000 < m ≤ 20000e  → ±1.0e
        (20_000, 100_000, Decimal('1.5')),   # 20000 < m ≤ 100000e → ±1.5e
    ],
    'III': [
        (0,      500,     Decimal('0.5')),   # 0 ≤ m ≤ 500e    → ±0.5e
        (500,    2_000,   Decimal('1.0')),   # 500 < m ≤ 2000e    → ±1.0e
        (2_000,  10_000,  Decimal('1.5')),   # 2000 < m ≤ 10000e  → ±1.5e
    ],
    'IIII': [
        (0,      50,      Decimal('0.5')),   # 0 ≤ m ≤ 50e     → ±0.5e
        (50,     200,     Decimal('1.0')),   # 50 < m ≤ 200e      → ±1.0e
        (200,    1_000,   Decimal('1.5')),   # 200 < m ≤ 1000e    → ±1.5e
    ],
}

def get_mpe(accuracy_class: str, load: Decimal, e: Decimal,
            verification_type: str = 'initial') -> Decimal:
    """
    Returns MPE as an absolute value in the instrument's unit.
    load = actual load in instrument units (g, kg, etc.)
    e = verification scale interval in same units
    verification_type = 'initial' or 'subsequent'
    """
    m = load / e  # express load in multiples of e
    for lower, upper, factor in MPE_TABLE[accuracy_class]:
        if lower < m <= upper or (lower == 0 and m == 0):
            mpe = factor * e
            if verification_type == 'subsequent':
                mpe = mpe * 2  # Section 3.5.2: in-service MPE = 2× initial
            return mpe
    raise ValueError(f"Load {load} out of range for class {accuracy_class}")
```

**Critical boundary behavior**: `0 ≤ m ≤ 500` means load of exactly 500e gets MPE=0.5e. Load of 501e gets MPE=1.0e. The first range uses `≤` on both ends; subsequent ranges use `<` on the lower bound and `≤` on the upper.

### Multi-interval instruments (Section 3.3) — WORKED EXAMPLE

Multi-interval ≠ multiple range. A multi-interval instrument has ONE weighing range divided into partial ranges with different e values. The range switches automatically based on applied load.

**Example from R-76 Section 3.3.1** (Class III):
```
Max = 15 kg, ranges: 2/5/15 kg, e = 1/2/10 g

Partial range 1: Min=20g,  Max1=2kg,   e1=1g,  n1=2000
Partial range 2: Min2=2kg, Max2=5kg,   e2=2g,  n2=2500
Partial range 3: Min3=5kg, Max3=15kg,  e3=10g, n3=1500

MPE calculation uses the CURRENT RANGE'S e, with load m divided by that e:

m = 0g    to 500g   → m/e1 = 0-500    → MPE = ±0.5 × e1 = ±0.5g
m > 500g  to 2000g  → m/e1 = 500-2000 → MPE = ±1.0 × e1 = ±1.0g
m > 2000g to 4000g  → m/e2 = 1000-2000→ MPE = ±1.0 × e2 = ±2.0g
m > 4000g to 5000g  → m/e2 = 2000-2500→ MPE = ±1.5 × e2 = ±3.0g
m > 5000g to 15000g → m/e3 = 500-1500 → MPE = ±1.0 × e3 = ±10.0g
```

**Implementation**: for a multi-interval instrument, first determine which partial range the load falls in (based on load vs Max_i boundaries). Use that range's e_i. Then compute m/e_i and look up Table 6.

### Multiple range instruments (Section 3.2)

Different from multi-interval. A multiple range instrument has two or more ranges each extending from ZERO to its own Max. Each range is treated as an independent instrument. The user manually selects the range.

Store as: `ranges = [{max: 3kg, e: 1g}, {max: 6kg, e: 2g}]`
MPE for each range calculated independently using that range's e and Max.

### Error calculation (Section T.5.5.1)

```python
# Error of indication (Section T.5.5.1):
# E = I - L
# where I = indicated value, L = conventional true value of the load

# For digital instruments, rounding error must be eliminated if d > 0.2e
# (Section 3.5.3.2). Use the half-division procedure from Annex A.4.4.3:
#
# If d > 0.2e:
#   Add small weights (about 0.1d each) until the display changes
#   from I to I + d. The indication just before change = P.
#   P = I + 0.5d - (added small weights)
#   E = P - L = (I + 0.5d - delta_L) - L
#
# If d ≤ 0.2e (most common case): E = I - L directly.
```

### Test procedures — CORRECTED DETAILS

**1. Weighing performance test (Annex A.4.4)**
- Apply loads in INCREASING order from zero to Max, then DECREASING back
- Test at minimum 5 points spread across each MPE zone boundary
- At each point: record indicated value, compute error, compare to MPE
- Both increasing and decreasing loads must independently meet MPE

**2. Eccentricity test (Section 3.6.2, Annex A.4.7)**
- Test load = 1/3 × (Max + T+), where T+ = maximum additive tare effect
- If no additive tare: test load = 1/3 × Max
- For rectangular platform: test at center + 4 positions (front-left, front-right, rear-left, rear-right)
- For circular platform: center + 4 quadrants
- For >4 support points: use 1/(n-1) × (Max + T+) at each support point
- For rolling loads (vehicle scales): 0.8 × (Max + T+)
- Each position's indication must meet MPE for that test load

**3. Repeatability test (Section 3.6.1, Annex A.4.10)**
- Same load placed on receptor multiple times under same conditions
- Minimum 3 repetitions; typically 6 for type evaluation
- At approximately 0.5×Max and near Max
- Range (max reading - min reading) must not exceed |MPE| for that load
- Each individual reading must also independently meet MPE

**4. Discrimination test (Section 3.8.2.2, Annex A.4.8)**
- FOR DIGITAL INSTRUMENTS ONLY (d ≥ 5mg):
  - Balance a load L until stable indication I
  - Gently deposit additional load = 1.4d
  - Indication must change unambiguously (I must become I+d or more)
  - Test at or near: Min, 0.5×Max, Max
  - Note: uses d (actual scale interval), NOT e

**5. Sensitivity test (Annex A.4.9)**
- For non-self-indicating instruments only (Section 6.1)
- Extra load of 0.4 × |MPE| (minimum 1mg) must produce visible displacement
- Self-indicating instruments: discrimination test covers this requirement

**6. Tare device test (Section 3.5.3.4, Annex A.4.6)**
- Tare weighing device MPE = same as instrument MPE for the same load value
- Test at several tare values across the tare range
- Verify net indication meets MPE for the net load
- MPE applies to net values for every possible tare load (Section 3.5.3.3)
- Exception: MPE does NOT apply to calculated net values (preset tare)

**7. Creep / time dependence test (Section 3.9.4.1, Annex A.4.11)**
- Apply load, read immediately, then at intervals over 30 minutes
- Requirement A: difference between initial and any reading within 30min ≤ 0.5e
- Requirement B: difference between 15-minute reading and 30-minute reading ≤ 0.2e
- If both A and B fail, extended test: total drift over 4 hours must not exceed |MPE|
- Applies to Class II, III, IIII only (not Class I)

**8. Zero return test (Section 3.9.4.2)**
- After removing load that has been on the instrument for 30 minutes
- Deviation from zero ≤ 0.5e (or 0.5×e1 for multi-interval)
- For multiple range: deviation from Maxi → zero ≤ 0.5×ei

**9. Temperature test (Section 3.9.2, Annex A.5.3)**
- Default operating range: −10°C to +40°C (if not specified on instrument)
- Minimum temperature range by class:
  - Class I: 5°C
  - Class II: 15°C
  - Class III/IIII: 30°C
- Temperature effect on zero (Section 3.9.2.3):
  - Class I: zero shall not vary by more than 1e per 1°C change
  - Class II/III/IIII: zero shall not vary by more than 1e per 5°C change
  - For multi-interval: uses e1 (smallest interval)

**10. Tilt test (Section 3.9.1.1, Annex A.5.1)**
- Applies to Class II, III, IIII only. NOT Class I (Section 3.9.1.2)
- Class I instruments must have a level indicator but need not be tested for tilt
- Tilt limit: defined by level indicator marking, or 50/1000 if no indicator
- At no load, tilted: indication change ≤ 2e (except Class II)
- At Max, tilted: error ≤ MPE (zeroed in both positions)

**11. Power supply variation test (Section 3.9.3, Annex A.5.4)**
- AC mains: lower = 0.85 × Unom, upper = 1.10 × Unom
  - (NOT ±15% — it's asymmetric: -15% / +10%)
- External DC/AC supply: lower = min operating voltage, upper = 1.20 × Unom
- Battery (non-rechargeable): lower = min operating, upper = Unom
- 12V vehicle battery: lower = min operating, upper = 16V
- 24V vehicle battery: lower = min operating, upper = 32V
- Instrument must either work correctly or show no weight values below min voltage

**12. Endurance / durability test (Section 3.9.4.3, Annex A.6)**
- ONLY for instruments with Max ≤ 100kg
- 100,000 load cycles at approximately 0.5 × Max
- After endurance: re-run full weighing performance test
- Durability error must not exceed |MPE|

**13. Span stability test (Section 5.4, Annex B.4)**
- For electronic instruments only
- Test load near Max, measured at intervals over a period
- Variation in errors during test must not exceed |MPE|

**14. Damp heat test (Annex B.2)**
- For electronic instruments only
- Steady state: 2 days at upper temperature limit, 85% relative humidity
- After conditioning: weighing performance test, errors ≤ MPE

**15. Disturbance tests (Annex B.3) — electronic instruments**
- Electrostatic discharge (ESD)
- Electromagnetic susceptibility (radiated)
- Electromagnetic susceptibility (conducted)
- Voltage dips and interruptions
- Bursts (transients)
- Surges
- Each disturbance: either no significant fault (>e) or instrument detects and acts

### Standard weights requirement (Section 3.7.1)

The standard weights used for testing must have error ≤ 1/3 of the instrument's MPE at the applied load. This affects the `correction` value in error calculations — the weight's known deviation from nominal is applied as a correction.

### Report format

A complete test report contains:
1. Header: lab name, accreditation, report number, date
2. Instrument details: manufacturer, model, serial, class, Max, Min, e, d, n, tare type, Lim
3. Environmental conditions: temperature range during test, humidity, pressure
4. Test observations: one table per test type (test point, reference, indicated, error, MPE, pass/fail)
5. For multi-interval: clearly identify which partial range each test point falls in
6. Summary: overall verdict — CONFORMS or DOES NOT CONFORM to R 76-1
7. Signatories: tested by, checked by, approved by (with dates)
8. Software identification: version of legally relevant software (Section 5.5, Annex G.4)

---

## Database rules

- Measurement values: `DecimalField(max_digits=15, decimal_places=6)`
- Serial number unique per manufacturer (compound constraint)
- Test sessions belong to one instrument + one laboratory
- Observations: soft-delete only
- Reports: versioned — regenerating creates v2, keeps v1
- Report numbers: `NAWI/{lab_code}/{YYYY}/{NNNN}` auto-sequential per lab per year
- Approved reports freeze underlying test data (pre-save check)
- Instrument model must store BOTH `d` (actual_scale_interval) and `e` (verification_scale_interval) as separate fields
- Instrument model stores `unit` (choices: mg, g, kg, t, ct)
- Multi-interval config stored as JSONB array: `[{max: 2000, e: 1}, {max: 5000, e: 2}, {max: 15000, e: 10}]`
- Multiple range config stored similarly, with `is_multi_interval` boolean to distinguish type
- Instrument model stores `max_additive_tare` (T+) for eccentricity test load calculation
- Instrument model stores `max_safe_load` (Lim)
- Creep test observations must record timestamps at 0, 15, and 30 minutes (not just values)

---

## API patterns

- Pagination: `?page=1&page_size=20&ordering=-created_at`
- Filters: `?accuracy_class=III&status=completed&date_from=2026-01-01`
- Search: `?search=` uses PostgreSQL full-text search
- Mutations return full serialized object
- Bulk observations: POST array, atomic save
- Report generation: async — returns 202 + task ID, poll for status

### Key endpoints

```
POST   /api/auth/login/
POST   /api/auth/refresh/
GET    /api/auth/me/

GET    /api/instruments/
POST   /api/instruments/
GET    /api/instruments/{id}/
GET    /api/instruments/{id}/tests/

POST   /api/sessions/
GET    /api/sessions/{id}/
POST   /api/sessions/{id}/observations/
POST   /api/sessions/{id}/calculate/
GET    /api/sessions/{id}/results/

POST   /api/reports/generate/{session_id}/
GET    /api/reports/{id}/
GET    /api/reports/{id}/download/pdf/
GET    /api/reports/{id}/download/docx/
POST   /api/reports/{id}/approve/
GET    /api/reports/search/?q=
```

---

## Environment variables

```bash
DJANGO_SECRET_KEY=
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://nawi:password@localhost:5432/nawi_db
REDIS_URL=redis://localhost:6379/0
REPORT_STORAGE_PATH=/var/nawi/reports/
ACCESS_TOKEN_LIFETIME_MINUTES=15
REFRESH_TOKEN_LIFETIME_DAYS=7
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
```

---

## Common pitfalls

- **Float arithmetic**: NEVER use `float`. Always `Decimal`. `0.1 + 0.2 != 0.3` matters at MPE boundaries.
- **MPE boundaries**: Table 6 uses `≤` on upper bounds. Load of exactly 500e for Class III → MPE = 0.5e (lower range), not 1.0e. Load of 501e → MPE = 1.0e. Get this one lookup wrong and every report for that class is invalid.
- **d vs e confusion**: Discrimination test uses `d` (actual scale interval). MPE table uses `e` (verification scale interval). For most instruments d = e, but for Class I/II with auxiliary devices d < e. Never substitute one for the other.
- **Multi-interval MPE**: Don't just divide load by e. First find which partial range the load falls in (comparing load to Max_i boundaries). Then use THAT range's e_i. Then compute m/e_i for Table 6 lookup. The worked example in Section 3.3 is the reference — implement it exactly.
- **Multi-interval vs multiple range**: Multi-interval = one range split into partials, auto-switching. Multiple range = separate ranges each starting from zero, user-selected. They are different instrument types stored differently and calculated differently.
- **Eccentricity test load**: It's 1/3 × (Max + T+), NOT 1/3 × Max. T+ is the maximum additive tare effect. If the instrument has no additive tare, then it simplifies to 1/3 × Max.
- **Power supply is asymmetric**: AC mains is 0.85×Unom to 1.10×Unom (−15% / +10%), NOT ±15%. The old CLAUDE.md had this wrong.
- **Creep thresholds**: Two separate checks — total drift over 30 min ≤ 0.5e AND drift between 15-30 min ≤ 0.2e. Both must pass. The system must record readings at 0, 15, and 30 minutes.
- **Discrimination threshold**: 1.4d, and ONLY for instruments with d ≥ 5mg. If d < 5mg, the discrimination test doesn't apply per Section 3.8.2.2.
- **Tilt test exclusion**: Class I instruments are NOT tested for tilt (Section 3.9.1.2). Don't show the tilt test form for Class I instruments.
- **Endurance test scope**: Only for instruments with Max ≤ 100kg (Section 3.9.4.3). Don't require it for weighbridges.
- **Min capacity validation**: Every test load must be ≥ Min. Observations at loads below Min should trigger a validation warning.
- **Rounding error elimination**: If d > 0.2e, the rounding error must be eliminated using the half-division procedure (Annex A.4.4.3). This affects how errors are computed for Class I/II instruments with auxiliary devices.
- **Verification type**: Default to initial verification but support both as a parameter. In-service MPE = 2× initial.
- **Unit consistency**: All calculations in the instrument's declared unit (kg, g, mg, t, ct). Never mix units mid-calculation. Store the unit alongside every value.
- **Report immutability**: Approved reports lock their test data. Enforce at model level with a pre-save check.
- **Ant Design defaults**: Override Ant Design's aggressive card shadows and colored backgrounds. Strip everything back to flat, borderless layouts per the UI rules above.
