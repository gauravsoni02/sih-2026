# ⚖️ NAWI Test Report Generator

### Digital Test, Calculation & Certification Platform for Non-Automatic Weighing Instruments

A comprehensive web-based application for **testing, evaluating, documenting, and generating compliance reports for Non-Automatic Weighing Instruments (NAWIs)** in accordance with **OIML Recommendation R 76-1:2006**.

The platform is designed for **Government Legal Metrology laboratories in India**, where inspectors and authorized metrology personnel need to evaluate weighing instruments such as electronic weighing scales, platform scales, industrial weighing systems, and weighbridges against prescribed metrological requirements.

Instead of relying on manually maintained spreadsheets, handwritten observation sheets, disconnected calculations, and manually formatted reports, the application provides a **single digital workflow** covering the complete lifecycle of a test:

> **Instrument Registration → Test Session → Observation Entry → Automatic OIML Calculations → Compliance Evaluation → Review → Report Generation → Audit Trail**

The system combines a domain-specific calculation engine implementing the relevant requirements of **OIML R 76-1:2006** with a modern React frontend, Django REST backend, PostgreSQL database, automated report generation, analytics, and audit logging.

---

# 📌 Table of Contents

* [Overview](#-overview)
* [Problem Statement](#-problem-statement)
* [Solution](#-solution)
* [Why NAWIs Matter](#-why-nawis-matter)
* [What the Application Does](#-what-the-application-does)
* [Core Workflow](#-core-workflow)
* [Major Features](#-major-features)
* [Supported Tests](#-supported-tests)
* [OIML R 76-1:2006 Calculation Engine](#-oiml-r-76-12006-calculation-engine)
* [MPE Calculation](#-mpe-calculation)
* [Accuracy Classes](#-accuracy-classes)
* [Multi-Interval Instruments](#-multi-interval-instruments)
* [d vs e](#-d-vs-e)
* [Error Calculation](#-error-calculation)
* [Compliance Evaluation](#-compliance-evaluation)
* [Architecture](#-architecture)
* [Backend](#-backend)
* [Frontend](#-frontend)
* [Database](#-database)
* [Calculation Engine](#-calculation-engine)
* [Report Generation](#-report-generation)
* [Dashboard & Analytics](#-dashboard--analytics)
* [Audit Trail](#-audit-trail)
* [Authentication & Authorization](#-authentication--authorization)
* [Offline & Device Integration](#-offline--device-integration)
* [Project Structure](#-project-structure)
* [Technology Stack](#-technology-stack)
* [API Architecture](#-api-architecture)
* [Validation](#-validation)
* [Testing](#-testing)
* [Decimal Arithmetic](#-decimal-arithmetic)
* [Security](#-security)
* [Installation](#-installation)
* [Quick Start](#-quick-start)
* [Docker Setup](#-docker-setup)
* [Environment Variables](#-environment-variables)
* [Development](#-development)
* [Production Deployment](#-production-deployment)
* [Example Workflow](#-example-workflow)
* [Report Contents](#-report-contents)
* [Design Principles](#-design-principles)
* [Advantages](#-advantages)
* [Future Roadmap](#-future-roadmap)
* [Project Status](#-project-status)
* [Contributing](#-contributing)
* [License](#-license)

---

# 🔎 Overview

Testing weighing instruments is not simply a matter of entering a measured value and checking whether it "looks close enough."

A legally relevant weighing instrument must satisfy specific metrological requirements. The permitted error depends on factors including:

* Accuracy class
* Verification scale interval (`e`)
* Actual scale interval (`d`)
* Applied load
* Instrument configuration
* Verification stage
* Whether the instrument is single-interval or multi-interval
* The specific test being performed

The application therefore treats the OIML recommendation as a **domain-specific calculation and compliance specification**, rather than merely using generic pass/fail thresholds.

The goal is to make the testing process:

* **Accurate**
* **Repeatable**
* **Traceable**
* **Auditable**
* **Standardized**
* **Fast**
* **Human-error resistant**
* **Suitable for formal reporting**

---

# 🚨 Problem Statement

Traditional weighing-instrument testing workflows often involve several disconnected tools and manual steps.

A typical process can involve:

1. Recording instrument information manually.
2. Recording environmental conditions.
3. Preparing test observations.
4. Applying loads to the instrument.
5. Writing observed values into paper forms or spreadsheets.
6. Manually calculating errors.
7. Looking up permissible maximum errors.
8. Comparing errors with the relevant limits.
9. Repeating the process for multiple test conditions.
10. Manually determining overall compliance.
11. Preparing a formal report.
12. Getting the report reviewed and signed.
13. Maintaining records for future inspection or audit.

This creates several opportunities for human error.

For example:

* A wrong MPE boundary can be selected.
* `d` may accidentally be used instead of `e`.
* A multi-interval range may be incorrectly identified.
* Decimal rounding may change a boundary result.
* Individual observations may be copied incorrectly.
* Calculations may be performed inconsistently.
* Reports may contain outdated templates.
* Historical changes may be difficult to trace.

The NAWI Test Report Generator attempts to eliminate these problems by putting the **instrument data, observations, calculations, compliance decisions, and final report into one controlled workflow**.

---

# 💡 Solution

The application provides a centralized digital testing platform where laboratory personnel can:

### 1. Register an instrument

Store all relevant instrument metadata.

### 2. Create a test session

Associate a particular testing procedure with a specific instrument.

### 3. Enter observations

Record readings and test-specific measurements.

### 4. Automatically calculate errors

The application performs the applicable mathematical calculations.

### 5. Determine MPE

The system identifies the relevant maximum permissible error based on the instrument configuration and applicable OIML requirements.

### 6. Provide live feedback

The frontend recalculates errors as observations are entered.

### 7. Determine compliance

Each observation and test can be evaluated against its applicable acceptance criteria.

### 8. Generate a formal report

A standardized report can be generated in PDF and DOCX formats.

### 9. Preserve an audit trail

Important changes are recorded for traceability.

---

# ⚖️ Why NAWIs Matter

**Non-Automatic Weighing Instruments (NAWIs)** are weighing instruments where an operator is involved in determining the weighing result.

Examples include:

* Retail weighing scales
* Laboratory weighing instruments
* Platform scales
* Industrial scales
* Counter scales
* Commercial weighing instruments
* Large-capacity weighing systems
* Weighbridges

These instruments can directly influence commercial transactions, industrial processes, quantity declarations, and regulatory measurements.

Consequently, ensuring that the instrument performs within prescribed metrological limits is important.

This project focuses on digitizing the testing and reporting workflow around those requirements.

---

# 🧩 What the Application Does

## Instrument Registration

Each instrument can have a structured digital profile containing information such as:

* Manufacturer
* Model
* Serial number
* Instrument type
* Accuracy class
* Maximum capacity
* Minimum capacity
* Scale interval (`d`)
* Verification scale interval (`e`)
* Number of intervals
* Multi-interval configuration
* Unit of measurement
* Identification information
* Verification stage

This information becomes the foundation for subsequent calculations.

---

# 🧪 Test Sessions

A test session represents a complete evaluation of an instrument.

A session can contain:

* Instrument identification
* Laboratory information
* Test date
* Environmental conditions
* Operator information
* Test configuration
* Test observations
* Calculated results
* Compliance status
* Reviewer information
* Report metadata

A session can therefore be treated as a complete, traceable testing record.

---

# 📝 Observation Entry

The application provides structured interfaces for entering observations.

Instead of maintaining separate spreadsheets for every test, observations are stored against the relevant:

* Instrument
* Test session
* Test type
* Load
* Indication
* Reference value
* Calculated error
* Permissible error
* Result

The frontend validates input while the backend remains responsible for authoritative calculations and persistence.

---

# ⚡ Live Error Feedback

One of the key usability features is real-time calculation.

As an operator enters an observation, the interface can immediately update:

* Load
* Indication
* Error
* Applicable MPE
* Difference from MPE
* Pass/fail status

This allows an operator to identify potentially problematic measurements immediately rather than waiting until the entire test is completed.

---

# 📊 Interactive Error vs Load Chart

The testing interface can visualize measurement error against applied load.

The graph contains:

* Actual measurement error
* Load
* MPE upper envelope
* MPE lower envelope
* Individual measurement points
* Pass/fail regions

Conceptually:

```text
Error
  ↑
MPE ───────────────────────
       •
          •
             •
0   ─────────────────────────→ Load
             •
         •
MPE ───────────────────────
```

This gives laboratory personnel an immediate visual representation of instrument performance across its weighing range.

---

# 🧪 Supported Tests

The platform is designed around the relevant tests required for evaluation of NAWIs.

The current implementation supports **13+ test categories**, including:

1. **Weighing Performance**
2. **Eccentricity**
3. **Repeatability**
4. **Discrimination**
5. **Sensitivity**
6. **Tare**
7. **Creep**
8. **Temperature**
9. **Tilt**
10. **Power Supply**
11. **Durability**
12. **Span Stability**
13. **Zero Tracking**

Each test has its own observation structure and calculation requirements.

The architecture deliberately avoids treating every test as an identical generic form because different tests have different:

* Inputs
* Calculations
* Acceptance criteria
* Observation structures
* Compliance rules

---

# 📐 OIML R 76-1:2006 Calculation Engine

The core of the application is the **pure calculation engine**.

The engine is intentionally separated from:

* Django views
* REST API logic
* Database models
* React components
* Report generation

This separation is important because regulatory calculations should not depend on presentation or HTTP-layer code.

The engine receives structured inputs and returns deterministic results.

Conceptually:

```text
Instrument Configuration
        │
        ▼
┌──────────────────────┐
│  Calculation Engine  │
│                      │
│  MPE lookup          │
│  Error calculation   │
│  Range detection     │
│  Test calculations   │
│  Compliance logic    │
└──────────┬───────────┘
           │
           ▼
     Calculation Result
```

The same engine can therefore be used by:

* REST APIs
* Test-session processing
* Report generation
* Automated tests
* Future CLI tools
* Future device integrations

---

# 📏 MPE Calculation

The application implements the **OIML R 76-1:2006 Table 6 MPE lookup**.

The lookup takes into account:

* Accuracy class
* Load range
* Verification scale interval (`e`)
* Verification stage

The engine uses **boundary-correct comparisons**.

For example, where an upper boundary is inclusive, the implementation uses:

```text
load ≤ boundary
```

rather than accidentally using:

```text
load < boundary
```

This distinction matters because measurements occurring exactly on a regulatory boundary must be evaluated according to the specification.

---

# 🎯 Accuracy Classes

The application supports all four NAWI accuracy classes:

* **Class I**
* **Class II**
* **Class III**
* **Class IIII**

The MPE calculation therefore does not use one universal tolerance.

Instead:

```text
Accuracy Class
       │
       ▼
Applicable MPE Table
       │
       ▼
Load Range
       │
       ▼
Permissible Error
```

This allows the same calculation engine to handle instruments with different accuracy requirements.

---

# 🔢 Multi-Interval Instruments

Multi-interval instruments require additional care.

A single instrument can have different scale intervals over different portions of its weighing range.

For example, conceptually:

```text
0 ─────────────  Max₁ ───────────── Max₂

    Range 1              Range 2

     e₁                    e₂
```

The application therefore determines which range contains the measurement and applies the corresponding `e`.

This prevents the system from incorrectly assuming that one scale interval applies across the entire weighing range.

The engine supports:

* Partial-range detection
* Per-range `e`
* Range boundary handling
* Multi-interval MPE evaluation

---

# 🔍 d vs e

A particularly important domain distinction is between:

### `d` — Actual Scale Interval

The actual displayed or indicated scale interval of the instrument.

### `e` — Verification Scale Interval

The verification scale interval used for metrological evaluation and MPE determination.

These values are **not interchangeable**.

The application explicitly models them separately.

For example:

```text
Instrument
│
├── d → actual scale interval
│
└── e → verification scale interval
```

This distinction is especially important because different tests use different quantities.

For example, the discrimination test is concerned with the instrument's actual scale behavior and therefore involves `d`, while MPE determination is based on `e`.

---

# 📐 Error Calculation

Measurement error is calculated from the relevant observation/reference values.

Conceptually:

```text
Error = Indicated Value - Reference Value
```

Depending on the specific test and procedure, the engine applies the appropriate calculation methodology.

The result can then be compared against the applicable MPE:

```text
|Error| ≤ MPE
```

If the applicable criterion is satisfied:

```text
PASS
```

Otherwise:

```text
FAIL
```

The system retains the calculated values rather than only storing a final boolean result.

This is important for traceability.

---

# ✅ Compliance Evaluation

Compliance is evaluated at multiple levels.

### Observation level

```text
Observation
     │
     ▼
Calculated Error
     │
     ▼
Applicable MPE
     │
     ▼
PASS / FAIL
```

### Test level

Multiple observations can contribute to a test result.

```text
Observation 1 ── PASS
Observation 2 ── PASS
Observation 3 ── PASS
Observation 4 ── PASS
       │
       ▼
   Test Result
```

### Session level

The complete test session can then produce an overall compliance result.

```text
Weighing Performance ─ PASS
Eccentricity          ─ PASS
Repeatability         ─ PASS
Discrimination        ─ PASS
...
                       │
                       ▼
                Overall Result
```

---

# 🏗️ Architecture

The application follows a layered architecture.

```text
                    ┌─────────────────────────┐
                    │      React Frontend     │
                    │                         │
                    │ Forms / Tables / Charts │
                    │ Zustand / React Query  │
                    └────────────┬────────────┘
                                 │
                              REST API
                                 │
                    ┌────────────▼────────────┐
                    │     Django Backend      │
                    │                         │
                    │ Authentication          │
                    │ Permissions             │
                    │ API endpoints           │
                    │ Validation              │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
       ┌────────────┐     ┌────────────┐     ┌────────────┐
       │ PostgreSQL │     │ Calculation│     │   Celery   │
       │            │     │   Engine   │     │   + Redis  │
       └────────────┘     └────────────┘     └────────────┘
                                 │
                                 ▼
                         Report Generation
                                 │
                         ┌───────┴────────┐
                         ▼                ▼
                       PDF              DOCX
```

---

# 🐍 Backend

The backend is built using:

* Python 3.12
* Django 5.x
* Django REST Framework 3.15

Django provides:

* Database models
* Authentication
* API infrastructure
* Validation
* Permissions
* Admin interface
* Application configuration

The backend is divided into domain-specific Django applications.

---

# ⚛️ Frontend

The frontend is built using:

* React 18
* TypeScript 5.5
* Vite
* Ant Design 5.x
* Zustand
* React Query

The frontend is responsible for:

* Navigation
* Forms
* Instrument registration
* Test interfaces
* Observation tables
* Live calculations
* Charts
* Report preview
* Dashboard
* Settings
* User experience

TypeScript provides strongly typed interfaces between frontend modules and API responses.

---

# 🗄️ Database

The production database is:

**PostgreSQL 16**

SQLite can be used during development.

The database stores structured information about:

* Users
* Laboratories
* Instruments
* Test sessions
* Tests
* Observations
* Results
* Reports
* Audit events

The database design separates instrument configuration from individual testing sessions so that an instrument can be tested repeatedly over its lifecycle.

---

# 🧮 Calculation Engine

The calculation engine lives independently inside:

```text
backend/apps/engine/
```

The engine is intentionally designed as a **pure domain layer**.

It should not depend on:

```text
Django request
HTTP request
React
Database connection
REST serializer
HTML
Report template
```

Instead:

```text
Input
  ↓
Pure Calculation
  ↓
Structured Result
```

This makes the domain logic:

* Easier to test
* Easier to review
* Easier to reuse
* Easier to validate
* Less coupled to infrastructure

---

# 📄 Report Generation

The application can generate formal test reports in:

* PDF
* DOCX

PDF generation uses:

* WeasyPrint
* ReportLab

DOCX generation uses:

* `python-docx`

Reports are designed to contain a formal laboratory document structure.

A report can include:

1. Government of India header
2. Laboratory information
3. Report identification
4. Instrument identification
5. Manufacturer
6. Model
7. Serial number
8. Accuracy class
9. Capacity
10. `d`
11. `e`
12. Environmental conditions
13. Test configuration
14. Test observations
15. Calculated errors
16. Applicable MPE
17. Test results
18. Overall compliance summary
19. Remarks
20. Signatory section

The report generator uses the same calculation results produced by the backend rather than independently reimplementing the domain calculations.

This avoids inconsistencies between the UI and final report.

---

# 🖨️ In-Browser Report Preview

Before generating the final document, the user can preview the report directly inside the browser.

The preview is designed to resemble a formal print document.

The preview can contain:

```text
┌─────────────────────────────────────┐
│       GOVERNMENT OF INDIA           │
│        LEGAL METROLOGY              │
│                                     │
│          TEST REPORT                │
├─────────────────────────────────────┤
│ Instrument Details                  │
│                                     │
│ Manufacturer: XXXXX                 │
│ Model: XXXXX                        │
│ Serial No: XXXXX                    │
├─────────────────────────────────────┤
│ Test Results                        │
│                                     │
│ Test       Result       Status      │
│ Weighing   ...          PASS        │
│ Eccentric  ...          PASS        │
├─────────────────────────────────────┤
│ Compliance Summary                  │
│                                     │
├─────────────────────────────────────┤
│ Signature                           │
└─────────────────────────────────────┘
```

This gives the operator an opportunity to review the final document before exporting it.

---

# 📊 Dashboard & Analytics

The dashboard provides a high-level overview of laboratory activity.

It includes metric cards for information such as:

* Total instruments
* Total test sessions
* Passed tests
* Failed tests
* Recent activity
* Testing trends

---

## Testing Trend Chart

The dashboard can visualize testing activity over time.

For example:

```text
Tests
 ↑
 │       █
 │   █   █     █
 │   █   █ █   █
 │ █ █   █ █   █
 └────────────────→
   Mon Tue Wed Thu
```

The system can distinguish between:

* Passed tests
* Failed tests

---

# 🥧 Pass/Fail Analytics

A pass/fail chart provides a quick overview of laboratory outcomes.

This is particularly useful for identifying:

* Failure rates
* Frequently failing tests
* Overall instrument compliance
* Trends across testing periods

---

# 📈 Measurement Error Profile

The dashboard can also expose measurement error behavior.

This provides a more meaningful engineering view than a simple pass/fail count.

Instead of only asking:

> "Did the instrument pass?"

the system can help answer:

> "How does measurement error behave across the weighing range?"

---

# 🧾 Activity Log

Every important action can be represented in an audit trail.

The activity log can capture events such as:

* Instrument created
* Instrument updated
* Test session created
* Observation modified
* Report generated
* Configuration changed
* User action performed

Events can be searched and filtered by severity.

Example:

```text
16:42  Instrument Updated       INFO
16:44  Test Session Created     INFO
16:51  Observation Added        INFO
16:57  MPE Evaluation           INFO
17:01  Test Failed             WARNING
17:05  Report Generated         INFO
```

This provides traceability when reviewing historical test activity.

---

# 🔐 Authentication & Authorization

Authentication is implemented using:

**djangorestframework-simplejwt**

The API can therefore use:

```text
Access Token
      +
Refresh Token
```

The backend also provides permission controls to prevent unauthorized operations.

The architecture allows permissions to be applied at the API and application levels.

---

# 👥 Laboratory-Oriented Access

The system is designed around a regulated laboratory workflow rather than a generic consumer application.

Different users may have different responsibilities, such as:

* Laboratory administrator
* Testing operator
* Reviewer
* Authorized signatory

The permission architecture allows such roles to be expanded as the project evolves.

---

# 🔌 Offline & Device Integration

The frontend includes service modules for:

* Offline storage
* Web Serial communication

This provides a foundation for eventually connecting supported weighing instruments directly to the application.

A future workflow could look like:

```text
Weighing Instrument
        │
        │ Serial / USB
        ▼
 Web Serial Interface
        │
        ▼
   React Application
        │
        ▼
 Observation Record
        │
        ▼
 Calculation Engine
```

Instead of manually typing every indication, a connected instrument could potentially provide the reading directly to the testing interface.

---

# 📁 Project Structure

```text
NAWI-Test-Report-Generator/
│
├── backend/
│   │
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   ├── asgi.py
│   │   └── celery.py
│   │
│   ├── common/
│   │   ├── models/
│   │   ├── pagination/
│   │   └── exceptions/
│   │
│   └── apps/
│       │
│       ├── accounts/
│       │   ├── models.py
│       │   ├── serializers.py
│       │   ├── views.py
│       │   ├── permissions.py
│       │   └── urls.py
│       │
│       ├── instruments/
│       │   ├── models.py
│       │   ├── serializers.py
│       │   ├── views.py
│       │   └── urls.py
│       │
│       ├── laboratory/
│       │   ├── models.py
│       │   ├── serializers.py
│       │   └── views.py
│       │
│       ├── testing/
│       │   ├── models.py
│       │   ├── serializers.py
│       │   ├── views.py
│       │   ├── services.py
│       │   └── urls.py
│       │
│       ├── engine/
│       │   ├── mpe.py
│       │   ├── errors.py
│       │   ├── eccentricity.py
│       │   ├── repeatability.py
│       │   ├── discrimination.py
│       │   ├── creep.py
│       │   ├── compliance.py
│       │   └── ...
│       │
│       ├── reports/
│       │   ├── pdf.py
│       │   ├── docx.py
│       │   ├── templates/
│       │   └── services.py
│       │
│       └── dashboard/
│           ├── views.py
│           ├── services.py
│           └── urls.py
│
├── frontend/
│   │
│   └── src/
│       │
│       ├── api/
│       │   ├── auth.ts
│       │   ├── instruments.ts
│       │   ├── testing.ts
│       │   ├── reports.ts
│       │   └── dashboard.ts
│       │
│       ├── components/
│       │   ├── Layout/
│       │   ├── Forms/
│       │   ├── Tables/
│       │   ├── Charts/
│       │   └── Common/
│       │
│       ├── pages/
│       │   ├── Dashboard/
│       │   ├── Instruments/
│       │   ├── Testing/
│       │   ├── Reports/
│       │   ├── Activity/
│       │   └── Settings/
│       │
│       ├── services/
│       │   ├── serial/
│       │   └── offline/
│       │
│       ├── store/
│       │   └── ...
│       │
│       ├── types/
│       │   └── ...
│       │
│       └── utils/
│           ├── mpe.ts
│           ├── validation.ts
│           └── demoData.ts
│
├── CLAUDE.md
├── docker-compose.yml
├── .env.example
├── README.md
└── LICENSE
```

---

# 🛠️ Technology Stack

| Layer             | Technology                 |
| ----------------- | -------------------------- |
| Backend Language  | Python 3.12                |
| Backend Framework | Django 5.x                 |
| API               | Django REST Framework 3.15 |
| Frontend          | React 18                   |
| Frontend Language | TypeScript 5.5             |
| Build Tool        | Vite                       |
| UI Framework      | Ant Design 5.x             |
| State Management  | Zustand                    |
| Server State      | React Query                |
| Charts            | Recharts                   |
| Database          | PostgreSQL 16              |
| Development DB    | SQLite                     |
| Task Queue        | Celery                     |
| Message Broker    | Redis                      |
| PDF               | WeasyPrint / ReportLab     |
| DOCX              | python-docx                |
| Authentication    | Simple JWT                 |
| Audit Logging     | django-auditlog            |
| Containerization  | Docker                     |
| Orchestration     | Docker Compose             |

---

# 🔌 API Architecture

The frontend communicates with the Django backend through REST APIs.

Conceptually:

```text
React
  │
  ├── GET    /api/instruments/
  ├── POST   /api/instruments/
  ├── GET    /api/testing/sessions/
  ├── POST   /api/testing/sessions/
  ├── POST   /api/testing/observations/
  ├── GET    /api/testing/results/
  ├── POST   /api/reports/generate/
  └── GET    /api/dashboard/
```

The exact endpoint structure can evolve as the application matures.

The API layer is responsible for:

* Authentication
* Serialization
* Validation
* Permissions
* Persistence
* Invoking domain services

The API layer should not contain the actual OIML calculation formulas.

---

# 🧹 Separation of Concerns

A major architectural principle is:

```text
UI ≠ API ≠ Domain Calculation ≠ Database ≠ Reports
```

For example:

### React

Responsible for:

```text
Display
Input
Interaction
Visualization
```

### Django REST API

Responsible for:

```text
HTTP
Authentication
Authorization
Serialization
Validation
```

### Calculation Engine

Responsible for:

```text
OIML calculations
MPE
Errors
Compliance
```

### Database

Responsible for:

```text
Persistence
Relationships
Historical records
```

### Reports

Responsible for:

```text
Formatting
Document generation
Printing
```

This makes the system easier to maintain and validate.

---

# 🧪 Validation

Input validation exists at multiple layers.

## Frontend Validation

Used to provide immediate user feedback.

Examples:

* Required fields
* Numeric values
* Valid capacities
* Valid scale intervals
* Valid accuracy class
* Valid test inputs

## Backend Validation

The backend performs authoritative validation before data is persisted.

This prevents clients from bypassing frontend checks.

## Domain Validation

The calculation engine validates domain-specific constraints.

For example:

```text
Instrument Configuration
        │
        ▼
Is configuration valid?
        │
   ┌────┴────┐
   │         │
  YES       NO
   │         │
Calculate   Reject
```

---

# 🧮 Decimal Arithmetic

Regulatory calculations must not depend on binary floating-point approximations when exact decimal boundaries matter.

The calculation engine therefore uses Python's:

```python
Decimal
```

rather than relying on ordinary binary floating-point arithmetic.

This is particularly important around MPE boundaries.

For example, a value that mathematically belongs exactly on a boundary should not accidentally become:

```text
boundary - 0.00000000001
```

because of floating-point representation.

The engine therefore performs relevant arithmetic using decimal representations.

---

# 🧪 Testing

The project currently contains **189 backend tests**.

These tests cover areas including:

* MPE boundaries
* Accuracy classes
* Multi-interval edge cases
* Error calculation
* Eccentricity
* Repeatability
* Discrimination
* Creep
* Compliance
* API permissions

The calculation engine is tested independently from the web interface.

---

# 🎯 Boundary Testing

Special attention is given to boundary conditions.

Examples include:

```text
load = lower boundary
load = upper boundary
load = upper boundary + smallest increment
load = upper boundary - smallest increment
```

This is especially important for regulatory tables where a single comparison operator can change the compliance result.

---

# 🧪 Test Philosophy

The project follows a principle of testing the **domain rules**, not merely the API endpoints.

A successful HTTP response does not prove that an OIML calculation is correct.

Therefore, the calculation engine receives direct unit tests.

Conceptually:

```text
Input
  ↓
Calculation
  ↓
Expected Result
```

rather than:

```text
HTTP Request
  ↓
HTTP 200
```

---

# 🔐 Security

The application includes several security-oriented components:

* JWT authentication
* Permission checks
* Backend validation
* Database-backed user management
* Audit logging
* Environment-based secrets
* Production database configuration
* Separation of configuration from source code

Sensitive configuration is stored through environment variables rather than being committed directly into the repository.

---

# 🚀 Installation

## Requirements

Recommended development environment:

```text
Python 3.12+
Node.js
npm
PostgreSQL 16
Redis
Git
```

Docker can be used instead of installing PostgreSQL and Redis manually.

---

# ⚡ Quick Start

## Backend

Navigate to the backend directory:

```bash
cd backend
```

Create and activate a Python environment:

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### Linux/macOS

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
python manage.py migrate
```

Create an administrator:

```bash
python manage.py createsuperuser
```

Start Django:

```bash
python manage.py runserver
```

The backend will normally be available at:

```text
http://localhost:8000
```

---

# ⚛️ Frontend Setup

Navigate to the frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend development server runs at:

```text
http://localhost:5173
```

API requests are proxied to:

```text
http://localhost:8000
```

---

# 🐳 Docker Setup

The project includes Docker Compose support.

Start the complete stack:

```bash
docker compose up -d
```

Run migrations:

```bash
docker compose exec web python manage.py migrate
```

Create a superuser:

```bash
docker compose exec web python manage.py createsuperuser
```

The resulting architecture can contain:

```text
┌──────────────┐
│   Frontend   │
└──────┬───────┘
       │
┌──────▼───────┐
│    Django    │
└───┬─────┬────┘
    │     │
    │     └────────────┐
    ▼                  ▼
PostgreSQL           Redis
                       │
                       ▼
                    Celery
```

---

# 🔧 Environment Variables

Copy:

```text
.env.example
```

to:

```text
.env
```

Then configure:

```env
DJANGO_SECRET_KEY=
DJANGO_DEBUG=True

DATABASE_URL=postgres://nawi:password@localhost:5432/nawi_db

REDIS_URL=redis://localhost:6379/0
```

For production, sensitive values should be supplied through the deployment environment rather than committed to source control.

---

# 🧑‍💻 Development

A typical development workflow is:

```text
1. Create/modify domain model
          ↓
2. Add/update migration
          ↓
3. Implement backend service
          ↓
4. Implement calculation logic
          ↓
5. Add unit tests
          ↓
6. Expose API endpoint
          ↓
7. Implement frontend API client
          ↓
8. Build UI
          ↓
9. Add integration tests
          ↓
10. Test complete workflow
```

The calculation engine should remain independent from UI changes.

---

# 🏭 Production Deployment

A production deployment can use:

```text
Reverse Proxy
     │
     ├── React static assets
     │
     └── Django API
            │
            ├── PostgreSQL
            ├── Redis
            └── Celery Workers
```

The application can be containerized to make deployment more reproducible.

Production configuration should include:

* `DEBUG=False`
* Secure secret key
* Production PostgreSQL
* Secure database credentials
* HTTPS
* Secure JWT configuration
* Proper CORS configuration
* Static file serving
* Persistent report storage
* Database backups
* Redis configuration
* Celery worker management

---

# 🔄 Example End-to-End Workflow

Consider a laboratory receiving an electronic weighing instrument.

## Step 1 — Register Instrument

The operator creates an instrument record:

```text
Manufacturer: Example Instruments
Model: EX-300
Serial No: EX300-001
Accuracy Class: III
Capacity: ...
d: ...
e: ...
```

---

## Step 2 — Create Test Session

The operator creates a new test session.

```text
Instrument
    ↓
Test Session
    ↓
Select applicable tests
```

---

## Step 3 — Record Environmental Conditions

The operator records relevant environmental conditions such as:

```text
Temperature
Humidity
Other required conditions
```

---

## Step 4 — Perform Tests

The operator works through the applicable tests.

For example:

```text
Weighing Performance
        ↓
Eccentricity
        ↓
Repeatability
        ↓
Discrimination
        ↓
Sensitivity
        ↓
...
```

---

## Step 5 — Enter Observations

The operator enters measurements into structured tables.

The system calculates the relevant values automatically.

---

## Step 6 — Determine MPE

The engine identifies:

```text
Accuracy Class
       +
Load
       +
Verification Interval
       +
Verification Stage
       ↓
Applicable MPE
```

---

## Step 7 — Evaluate Compliance

The calculated error is compared with the applicable permissible error.

```text
Calculated Error
       │
       ▼
Applicable MPE
       │
       ▼
┌───────────────┐
│ Within limit? │
└───────┬───────┘
        │
   ┌────┴────┐
   ▼         ▼
 PASS       FAIL
```

---

## Step 8 — Review

The operator or reviewer can inspect:

* Individual observations
* Calculated errors
* MPE values
* Test outcomes
* Overall compliance

---

## Step 9 — Generate Report

The system generates:

```text
PDF
```

and/or:

```text
DOCX
```

containing the complete testing record.

---

## Step 10 — Preserve Audit Trail

The system records relevant actions for future reference.

The result is a complete digital test record.

---

# 📄 Report Contents

A generated report can contain the following structure:

```text
================================================
               GOVERNMENT OF INDIA
                 LEGAL METROLOGY

                  TEST REPORT
================================================

REPORT INFORMATION

Report Number:
Date:
Laboratory:

------------------------------------------------

INSTRUMENT INFORMATION

Manufacturer:
Model:
Serial Number:
Accuracy Class:
Maximum Capacity:
Minimum Capacity:
Scale Interval (d):
Verification Scale Interval (e):

------------------------------------------------

ENVIRONMENTAL CONDITIONS

Temperature:
Humidity:
Other Conditions:

------------------------------------------------

TEST RESULTS

Test Name
Observation
Calculated Error
Applicable MPE
Result

------------------------------------------------

COMPLIANCE SUMMARY

Total Tests:
Passed:
Failed:
Overall Status:

------------------------------------------------

REMARKS

...

------------------------------------------------

SIGNATORY

Tested By:
Reviewed By:
Authorized Signatory:

================================================
```

The final format can be customized according to laboratory and organizational requirements.

---

# 🧠 Design Principles

## 1. Domain-first

The application is built around the actual metrological requirements rather than forcing the domain into a generic CRUD application.

---

## 2. Deterministic calculations

Given the same valid inputs, the calculation engine should produce the same result.

```text
Input A → Result A
Input A → Result A
Input A → Result A
```

---

## 3. Traceability

A compliance result should not be a mysterious boolean.

The system retains the underlying:

```text
Input
  ↓
Calculation
  ↓
MPE
  ↓
Comparison
  ↓
Result
```

---

## 4. Separation of concerns

Calculation logic should not be mixed with:

* React components
* Django views
* Report templates
* Database queries

---

## 5. Human-error reduction

The software should prevent avoidable mistakes wherever possible through:

* Validation
* Automatic calculations
* Structured forms
* Standardized reports
* Boundary-aware MPE lookup
* Audit trails

---

## 6. Regulatory accuracy

The calculation engine should prioritize correctness over convenience.

A visually attractive interface is useful, but the most important component is the correctness of the metrological calculations.

---

# 🚀 Advantages

## Before

```text
Paper
  +
Spreadsheet
  +
Manual MPE lookup
  +
Manual calculation
  +
Manual report formatting
  +
Separate record keeping
```

## After

```text
                 ┌───────────────────┐
                 │ NAWI Test Platform│
                 └─────────┬─────────┘
                           │
       ┌───────────┬───────┼────────┬───────────┐
       ▼           ▼       ▼        ▼           ▼
   Instrument    Testing  Engine   Reports    Audit
   Registry      Sessions         Generator   Log
                   │
                   ▼
               Compliance
```

The result is a single integrated workflow.

---

# 📈 Future Roadmap

The architecture allows the platform to grow beyond the current implementation.

Potential future additions include:

## 🔌 Direct Instrument Connectivity

Expand Web Serial/device support for automatic reading acquisition.

```text
Scale
 ↓
USB / Serial
 ↓
Browser
 ↓
Observation
```

---

## 📱 Mobile/Tablet Support

Provide responsive interfaces for laboratory environments where operators may not always use desktop computers.

---

## ☁️ Centralized Laboratory Network

Multiple laboratories could potentially synchronize data through a centralized infrastructure.

```text
Laboratory A ─┐
Laboratory B ─┼──► Central System
Laboratory C ─┤
Laboratory D ─┘
```

---

## 📊 Advanced Analytics

Potential analytics include:

* Failure trends by manufacturer
* Failure trends by model
* Test-specific failure rates
* Instrument history
* Laboratory workload
* Measurement error distributions
* Historical compliance trends

---

## 📜 Certificate Management

Future versions could support:

* Certificate numbering
* Certificate renewal
* Verification history
* Expiry tracking
* QR-based certificate verification

---

## 🔎 QR Verification

A generated certificate could contain a QR code allowing authorized users to verify the authenticity of the report.

Conceptually:

```text
Certificate
     │
     ▼
    QR
     │
     ▼
Verification Portal
     │
     ▼
Authenticity + Report Status
```

---

## 🧠 Intelligent Assistance

A future version could provide domain-aware assistance for:

* Identifying missing observations
* Detecting inconsistent entries
* Highlighting suspicious measurement patterns
* Explaining calculation results
* Assisting report review

Such assistance would remain separate from the authoritative calculation engine.

---

# 🏆 Project Objective

The ultimate objective of the NAWI Test Report Generator is to transform the traditional weighing-instrument testing workflow into a **digitized, standardized, traceable, and calculation-driven system**.

Instead of treating testing as:

```text
Measure → Write → Calculate → Compare → Type Report
```

the platform turns it into:

```text
Register
   ↓
Configure
   ↓
Measure
   ↓
Calculate Automatically
   ↓
Evaluate
   ↓
Review
   ↓
Generate
   ↓
Audit
```

The application therefore acts not merely as a form-filling tool, but as a **domain-specific metrology platform** built around the requirements of OIML R 76-1:2006.

---

# 📌 Project Status

The project currently includes:

* ✅ Instrument registration
* ✅ Test session management
* ✅ 13+ test categories
* ✅ OIML R 76-1:2006 MPE calculation
* ✅ Four accuracy classes
* ✅ Multi-interval support
* ✅ `d` / `e` distinction
* ✅ Decimal arithmetic
* ✅ Automatic error calculation
* ✅ Live frontend feedback
* ✅ Error-vs-load visualization
* ✅ Compliance evaluation
* ✅ PDF generation
* ✅ DOCX generation
* ✅ In-browser report preview
* ✅ Dashboard analytics
* ✅ Activity/audit log
* ✅ JWT authentication
* ✅ API permissions
* ✅ Docker support
* ✅ PostgreSQL support
* ✅ Redis/Celery infrastructure
* ✅ 189 backend tests

---

# 🤝 Contributing

Contributions are welcome.

When contributing to the calculation engine, changes should be accompanied by appropriate tests covering:

* Normal cases
* Boundary cases
* Invalid inputs
* Accuracy-class differences
* Multi-interval behavior
* Compliance outcomes

For frontend changes, contributors should ensure that:

* Existing workflows remain functional
* API types remain synchronized
* Forms validate correctly
* Calculation results remain consistent with backend results

---

# 📜 License

This project is released under the **MIT License**.

See:

```text
LICENSE
```

for the complete license text.

---

# ⭐ Summary

**NAWI Test Report Generator** is a full-stack digital metrology platform designed to simplify the testing and reporting of **Non-Automatic Weighing Instruments**.

It combines:

```text
        OIML R 76-1:2006
                │
                ▼
       ┌─────────────────┐
       │ Calculation     │
       │ Engine          │
       └────────┬────────┘
                │
        ┌───────┴────────┐
        ▼                ▼
     Backend          Frontend
        │                │
        └───────┬────────┘
                ▼
          Test Sessions
                │
                ▼
          Compliance
                │
          ┌─────┴─────┐
          ▼           ▼
         PDF         DOCX
                │
                ▼
           Audit Trail
```

The system is designed to reduce manual calculation, improve consistency, standardize reporting, and provide a complete digital record of the testing process.

**From instrument registration to final certification-ready documentation, the entire workflow is brought into one application.**
