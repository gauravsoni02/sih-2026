# NAWI Enhancement Prompt

You are working on an existing, already-built NAWI Test Report System. The project has been developed through all phases and has working features. **Do NOT scaffold, restructure, or rewrite from scratch.** Read the existing codebase first, understand what's already there, then enhance it.

## Step 1 — Audit the existing project

Before writing any code, do this:

```
1. Read CLAUDE.md to understand the project spec and domain knowledge
2. List all existing frontend pages and routes
3. List all existing backend API endpoints
4. List all existing components
5. Identify the current tech stack (check package.json, requirements.txt)
6. Note what state management, UI library, and styling approach is in use
7. Summarize what's already working
```

Print the audit results before proceeding. Do not assume anything — read the actual code.

## Step 2 — Study the reference frontend

There is a reference frontend at `nawi-ref/nawi-frontend/src/`. It is a static demo with mock data (no real backend), but it demonstrates excellent UI patterns and features. Study these files:

**Architecture & patterns:**
- `src/App.tsx` — route structure with lazy loading
- `src/components/layout/Sidebar.tsx` — collapsible sidebar design
- `src/components/layout/AppLayout.tsx` — shell layout
- `src/types/models.ts` — data type definitions
- `src/services/serial/web-serial.ts` — Web Serial instrument connection
- `src/services/storage/offline-storage.ts` — IndexedDB offline storage
- `src/utils/measurements.ts` — measurement row generation and formatting

**Key pages to study:**
- `src/components/dashboard/DashboardPage.tsx` — rich dashboard with metric cards, charts, active test card
- `src/components/dashboard/MeasurementErrorChart.tsx` — error vs load chart with MPE envelope
- `src/components/testing/NewTestPage.tsx` — 10-step test wizard
- `src/components/testing/TestStepper.tsx` — step progress bar
- `src/components/testing/TestExecutionPage.tsx` — inline editable measurement table with live error calculation + error chart + serial connection panel
- `src/components/instruments/InstrumentsPage.tsx` — searchable instrument register with inline actions
- `src/components/instruments/InstrumentEditorDialog.tsx` — modal for create/edit instrument
- `src/components/reports/ReportPreviewPage.tsx` — print-ready formal report preview
- `src/components/audit/AuditLogPage.tsx` — audit trail with severity filtering
- `src/components/settings/SettingsPage.tsx` — tabbed settings (profile, lab, preferences, reports, connections, about)
- `src/components/common/*` — reusable components (MetricCard, StatusBadge, PageHeader, EmptyState, FormSection, ConfirmDialog, Alert)

## Step 3 — Gap analysis and enhancement plan

Compare what exists in the project against the reference. For each feature below, check if it already exists, partially exists, or is missing. Then implement only what's missing, adapting it to the existing tech stack and patterns.

### Feature checklist

**Dashboard enhancements:**
- [ ] Metric cards with trend indicators (value + change + arrow direction + color)
- [ ] Active test card (shows in-progress test with step progress bar)
- [ ] Laboratory readiness card (system service statuses: API/DB/serial — online/offline/syncing)
- [ ] Testing trend chart (monthly pass/fail bar chart, last 6 months)
- [ ] Pass/fail pie chart (current month distribution)
- [ ] Measurement error vs nominal load chart with MPE envelope (blue error line, orange dashed ±MPE lines, zero reference line) — this is the signature visualization
- [ ] Quick action buttons in dashboard header (start test, register instrument, review reports)

**Instrument register enhancements:**
- [ ] Search bar with real-time filtering across ID, manufacturer, serial, owner
- [ ] Status filter dropdown (all/active/due-soon/attention/archived)
- [ ] Inline action buttons per row (view/edit/archive) with icon buttons
- [ ] Archive with confirm dialog
- [ ] Instrument editor as a modal dialog (not a separate page) for both create and edit
- [ ] Instrument detail page showing full specs as key-value definition list + test history for that instrument
- [ ] "Next test due" tracking per instrument

**Test workflow enhancements:**
- [ ] 10-step test stepper (horizontal progress bar with numbered circles, completed=green check, active=blue, upcoming=gray)
- [ ] Steps: Select instrument → Test info → Environment → Zero checks → Repeatability → Eccentricity → Accuracy → Additional tests → Review → Complete
- [ ] Save draft button that persists to offline storage (IndexedDB)
- [ ] Each step has: step counter, title, description, form content
- [ ] Previous/Next navigation at bottom
- [ ] "Continue later" option

**Test execution page (the most important screen):**
- [ ] Two-column layout: wide left (data) + narrow right sidebar (summary)
- [ ] Instrument context card at top (instrument, capacity, class, officer, date, conditions, reference, status as key-value pairs)
- [ ] Editable measurement table with inline `<input type="number">` in the Indicated Value column
- [ ] Live error calculation: `error = indicated - reference`, auto-computed on every keystroke
- [ ] Live result determination: `|error| ≤ MPE → pass, else fail`, shown as colored text/badge per row
- [ ] Monospace tabular-nums for all numeric table columns
- [ ] Error vs nominal load chart below the table (updates live as values are entered)
- [ ] Right sidebar: test summary card (passed/failed/warnings counts + overall result)
- [ ] Right sidebar: instrument connection card with Web Serial API
- [ ] Right sidebar: decision guidance card (warning about review requirement)
- [ ] Header actions: Exit, Save draft, Complete test (with confirm dialog)

**Web Serial integration (new feature):**
- [ ] `WebSerialService` class: connect(baudRate), disconnect(), readMeasurement()
- [ ] Uses `navigator.serial.requestPort()` for USB instrument connection
- [ ] Connection states: unsupported, disconnected, connecting, connected, error
- [ ] Graceful degradation — disable button and show message if browser doesn't support Web Serial
- [ ] "Connect instrument" button in the test execution sidebar
- [ ] Configurable baud rate (default 9600)

**Offline storage (new feature):**
- [ ] `OfflineStorage` class wrapping IndexedDB with localStorage fallback
- [ ] Stores: instruments, tests, drafts, reports, settings
- [ ] Save test drafts locally so work isn't lost on network failure
- [ ] Cache instrument data for offline access
- [ ] Persist user settings/preferences locally

**Report preview enhancements:**
- [ ] In-browser print-ready report layout (not just download PDF)
- [ ] Formal government header: "Government of India · Department of Consumer Affairs"
- [ ] Sub-header: "Legal Metrology Laboratory · NAWI Examination and Test Report · OIML R 76 Compliance"
- [ ] Report number + version + date + status in header
- [ ] Two-column section: Instrument identification | Test information
- [ ] Full measurement results table with cell borders (print-friendly style)
- [ ] Conclusion section with overall result + narrative text
- [ ] Authorization section with signature line and officer name
- [ ] Footer: document ID + generation source + page count
- [ ] Print button (`window.print()`) + Download PDF button
- [ ] Print-specific CSS (use `print:` variants or `@media print`) — hide nav, remove shadows/borders

**Audit log enhancements:**
- [ ] Search across all fields (user, action, entity, description)
- [ ] Severity filter (all/info/warning/critical)
- [ ] Severity badges with colors (blue=info, amber=warning, red=critical)
- [ ] Device/IP column
- [ ] Monospace timestamps

**Settings page enhancements:**
- [ ] Left sidebar navigation with 6 tabs (not top tabs):
  - Profile (name, role, department, initials)
  - Laboratory (lab name, jurisdiction, address, report prefix)
  - Preferences (default unit, stabilization period, default accuracy class, report version)
  - Report settings (number pattern, default review status, signature placement, retention note)
  - Connections (API URL, serial baud rate, offline storage status indicator)
  - About (app version, tech stack, offline mode status, serial capability)
- [ ] Save preferences button in header
- [ ] Success alert on save

**Shared component enhancements:**
- [ ] `PageHeader` — title + description text + right-aligned action buttons slot
- [ ] `MetricCard` — label (uppercase, xs), big value (2xl, semibold, tabular-nums), change indicator with directional arrow
- [ ] `StatusBadge` — consistent badge for pass/fail/warning/pending/active/due-soon/archived/online/offline/syncing/draft/awaiting-review/signed/generated
- [ ] `EmptyState` — icon + title + description centered in empty tables/lists
- [ ] `FormSection` — title + description + children for grouped form fields
- [ ] `ConfirmDialog` — modal with title, description, cancel button, confirm button (destructive styling)
- [ ] `Alert` — inline banner with tone variants (info=blue, success=green, warning=amber, error=red)
- [ ] `LoadingState` — centered spinner with text label
- [ ] `SectionHeader` — reusable card/section header

## Rules for implementation

1. **Match the existing patterns.** If the project uses Ant Design, build new features with Ant Design. If it uses Tailwind, use Tailwind. Don't introduce a new UI library.
2. **Wire to real API.** The reference uses mock data (`SERVICES/api/mock-data.ts`). Your features must call real Django backend endpoints. If an endpoint doesn't exist yet, create it.
3. **Keep the minimalist aesthetic.** The reference uses slate-gray palette, subtle borders, monospace numbers, minimal color. Match that tone even if adapting components to a different UI library.
4. **Don't break existing features.** Run the app after each enhancement to verify nothing regressed.
5. **One feature at a time.** Don't try to add everything in one pass. Work through the checklist above top-to-bottom. After each feature, verify it works.
6. **Adapt the MPE calculation.** The reference's `createMeasurementRows` and `updateIndicatedValue` use simplified JavaScript math. Our backend engine has the real R-76 calculation. For the frontend, use the backend API for MPE values, but do the `error = indicated - reference` and `|error| ≤ mpe` comparison client-side for instant feedback, then validate server-side on save.
7. **The error chart is non-negotiable.** The measurement error vs nominal load chart with the MPE envelope is the most valuable visualization. It must appear on: the dashboard (for the most recent/active test), the test execution page (live-updating), and the test results page (read-only).
