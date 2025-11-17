# DataHarbour - Clean Project Structure

> **Last Updated:** 2025-01-15
> **Status:** Production Ready ✅

## 📂 Project Tree

```
dataharbour/
├── 📁 backend/                         # FastAPI Backend Application
│   ├── 📁 app/
│   │   ├── 📁 api/
│   │   │   ├── 📁 v1/
│   │   │   │   ├── 📁 endpoints/       # API route handlers
│   │   │   │   │   ├── dashboard.py    # Dashboard stats & trends
│   │   │   │   │   ├── jobs.py         # Spark job management
│   │   │   │   │   ├── clusters.py     # Cluster management
│   │   │   │   │   ├── notebooks.py    # Notebook CRUD
│   │   │   │   │   └── monitoring.py   # System monitoring
│   │   │   │   └── __init__.py         # Router registration
│   │   │   └── __init__.py
│   │   ├── 📁 core/
│   │   │   ├── config.py               # Configuration & settings
│   │   │   ├── security.py             # Security utilities
│   │   │   └── websocket_manager.py    # WebSocket connection manager
│   │   ├── 📁 middleware/
│   │   │   ├── rate_limit.py           # Rate limiting (60 req/min)
│   │   │   ├── security_headers.py     # Security headers middleware
│   │   │   └── audit_log.py            # Audit logging
│   │   ├── 📁 models/
│   │   │   ├── job.py                  # Job schemas
│   │   │   ├── notebook.py             # Notebook schemas
│   │   │   └── cluster.py              # Cluster schemas
│   │   ├── 📁 services/
│   │   │   ├── spark_service.py        # Spark integration
│   │   │   ├── job_service.py          # Job management logic
│   │   │   ├── notebook_service.py     # Notebook management
│   │   │   └── monitoring_service.py   # System monitoring
│   │   ├── main.py                     # FastAPI app entry point
│   │   └── __init__.py
│   ├── 📁 tests/                       # Backend tests (70%+ coverage)
│   │   ├── 📁 test_api/
│   │   │   ├── test_dashboard.py       # Dashboard endpoint tests
│   │   │   ├── test_jobs.py            # Jobs API tests
│   │   │   └── __init__.py
│   │   ├── test_security.py            # Security tests
│   │   ├── conftest.py                 # Test fixtures
│   │   └── __init__.py
│   ├── requirements.txt                # Production dependencies
│   ├── requirements-dev.txt            # Development dependencies
│   ├── pytest.ini                      # Pytest configuration
│   ├── Dockerfile                      # Backend container
│   ├── README.md                       # Backend documentation
│   └── API_QUICKSTART.md               # API quick reference
│
├── 📁 frontend/                        # React Frontend Application
│   ├── 📁 public/                      # Static assets
│   ├── 📁 src/
│   │   ├── 📁 components/
│   │   │   ├── 📁 layout/
│   │   │   │   ├── Layout.jsx          # Main layout wrapper
│   │   │   │   ├── Sidebar.jsx         # Navigation sidebar
│   │   │   │   └── Header.jsx          # Page header
│   │   │   └── 📁 ui/
│   │   │       ├── Button.jsx          # Reusable button
│   │   │       ├── Card.jsx            # Card container
│   │   │       ├── Modal.jsx           # Dialog component
│   │   │       └── Badge.jsx           # Status badges
│   │   ├── 📁 pages/
│   │   │   ├── Dashboard.jsx           # Dashboard page
│   │   │   ├── Jobs.jsx                # Job management
│   │   │   ├── Notebooks.jsx           # Notebook management
│   │   │   ├── Clusters.jsx            # Cluster management
│   │   │   ├── Monitoring.jsx          # Monitoring page
│   │   │   └── Settings.jsx            # Settings page
│   │   ├── 📁 services/
│   │   │   ├── api.js                  # Axios API client
│   │   │   └── websocket.js            # WebSocket service
│   │   ├── 📁 store/
│   │   │   └── useStore.js             # Zustand state management
│   │   ├── 📁 tests/
│   │   │   ├── setup.js                # Test setup
│   │   │   └── 📁 components/
│   │   ├── App.jsx                     # Root component
│   │   ├── main.jsx                    # React entry point
│   │   └── index.css                   # Global styles
│   ├── package.json                    # NPM dependencies
│   ├── vite.config.js                  # Vite configuration
│   ├── tailwind.config.js              # Tailwind CSS config
│   ├── vitest.config.js                # Vitest test config
│   ├── index.html                      # HTML template
│   ├── Dockerfile                      # Frontend container
│   └── README.md                       # Frontend documentation
│
├── 📁 scripts/                         # Utility Scripts
│   ├── generate-secrets.sh             # Generate secure passwords
│   ├── backup.sh                       # Database backup script
│   └── restore.sh                      # Restore from backup
│
├── 📁 docs/                            # Documentation
│   ├── TRACK1_IMPLEMENTATION.md        # Backend API implementation
│   ├── TRACK2_IMPLEMENTATION.md        # Frontend refactor guide
│   ├── TRACK3_IMPLEMENTATION.md        # Security hardening guide
│   ├── TRACK4_IMPLEMENTATION.md        # Testing & quality guide
│   ├── TRACK5_IMPLEMENTATION.md        # DevOps & documentation
│   ├── SECURITY_AUDIT.md               # Security assessment
│   └── PROJECT_SUMMARY.md              # Complete project overview
│
├── 📁 .github/
│   └── 📁 workflows/
│       └── ci.yml                      # CI/CD pipeline
│
├── 📁 data/                            # Data persistence (gitignored)
│   ├── 📁 spark/                       # Spark data
│   ├── 📁 jupyter/                     # Jupyter notebooks
│   ├── 📁 postgres/                    # PostgreSQL data
│   ├── 📁 minio/                       # MinIO object storage
│   ├── 📁 airflow/                     # Airflow DAGs
│   └── 📁 logs/                        # Application logs
│
├── 📁 component/                       # Shared assets
│   └── LOGO-white.svg                  # Project logo
│
├── docker-compose.yml                  # Base docker configuration
├── docker-compose.secure.yml           # Production security config
├── Dockerfile                          # Spark service Dockerfile
├── .env.example                        # Environment template
├── .gitignore                          # Git ignore rules
├── .pre-commit-config.yaml             # Pre-commit hooks
├── README.md                           # Main project documentation
└── STRUCTURE.md                        # This file
```

## 🗂️ Directory Descriptions

### `/backend` - FastAPI Backend
**Purpose:** REST API server with 30+ endpoints, WebSocket support, and Spark integration

**Key Files:**
- `app/main.py` - FastAPI application with middleware stack
- `app/api/v1/endpoints/` - API route handlers
- `app/services/` - Business logic layer
- `app/middleware/` - Security middleware (rate limit, headers, audit)
- `tests/` - Comprehensive test suite

**Technologies:** FastAPI, Uvicorn, Pydantic, PySpark, WebSocket

### `/frontend` - React Frontend
**Purpose:** Modern web interface for DataHarbour platform

**Key Files:**
- `src/App.jsx` - Root component with routing
- `src/pages/` - Page components (Dashboard, Jobs, etc.)
- `src/components/` - Reusable UI components
- `src/services/api.js` - API client with axios
- `src/store/useStore.js` - Zustand state management

**Technologies:** React 18, Vite, Tailwind CSS, Zustand, React Router

### `/scripts` - Utility Scripts
**Purpose:** Automation and maintenance scripts

**Scripts:**
- `generate-secrets.sh` - Generate secure random passwords for production
- `backup.sh` - Automated backup of PostgreSQL, MinIO, notebooks
- `restore.sh` - Restore from backup archive

### `/docs` - Documentation
**Purpose:** Comprehensive project documentation

**Documents:**
- Track implementation guides (1-5)
- Security audit report
- Project summary with statistics
- All documentation is markdown for easy versioning

### `/data` - Data Persistence
**Purpose:** Docker volume mounts for persistent data (gitignored)

**Subdirectories:**
- `spark/` - Spark job data and checkpoints
- `jupyter/` - Saved Jupyter notebooks
- `postgres/` - PostgreSQL database files
- `minio/` - Object storage data
- `airflow/` - Airflow DAGs and logs
- `logs/` - Application audit logs (JSON format)

## 🔧 Configuration Files

### Docker Configuration
| File | Purpose |
|------|---------|
| `docker-compose.yml` | Base development configuration |
| `docker-compose.secure.yml` | Production security overlay |
| `Dockerfile` (root) | Spark service container |
| `backend/Dockerfile` | FastAPI backend container |
| `frontend/Dockerfile` | Nginx + React build container |

### Environment & Secrets
| File | Purpose |
|------|---------|
| `.env.example` | Template for environment variables |
| `.env` | Actual secrets (gitignored, generate with script) |

### CI/CD & Quality
| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | GitHub Actions pipeline |
| `.pre-commit-config.yaml` | Pre-commit hooks (Black, flake8, Prettier) |
| `backend/pytest.ini` | Pytest configuration (70% coverage) |
| `frontend/vitest.config.js` | Vitest configuration |

### Git Configuration
| File | Purpose |
|------|---------|
| `.gitignore` | Excludes: .env, data/, secrets, certificates |

## 📊 File Statistics

| Category | Count |
|----------|-------|
| **Total Files** | 120+ |
| **Backend Files** | 35+ |
| **Frontend Files** | 55+ |
| **Test Files** | 15+ |
| **Documentation Files** | 10+ |
| **Config Files** | 10+ |

## 🧹 Cleanup Summary

### ✅ Removed (Redundant)
- `dashboard/` directory (legacy 1317-line HTML file)
- `dashboard-legacy` service from docker-compose.yml

### ✅ Organized
- All implementation docs moved to `docs/` directory
- Clear separation of backend/frontend/scripts/docs
- Logical grouping of related files

### ✅ Retained (Essential)
- All backend API code
- Complete React frontend
- Security middleware and utilities
- Comprehensive test suite
- All documentation (now in `docs/`)
- CI/CD pipeline
- Docker configurations

## 🎯 Quick Access

### Start Development
```bash
docker-compose up -d
```

### Access Services
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Run Tests
```bash
# Backend
cd backend && pytest --cov=app

# Frontend
cd frontend && npm run test:coverage
```

### Deploy Production
```bash
bash scripts/generate-secrets.sh > .env
docker-compose -f docker-compose.yml -f docker-compose.secure.yml up -d
```

## 📝 File Naming Conventions

### Python Files
- **Snake case:** `job_service.py`, `rate_limit.py`
- **Test files:** `test_*.py`
- **Init files:** `__init__.py` for packages

### JavaScript Files
- **PascalCase:** `Dashboard.jsx`, `Button.jsx` (components)
- **camelCase:** `api.js`, `websocket.js` (services)
- **Test files:** `*.test.jsx`

### Documentation
- **UPPERCASE.md:** `README.md`, `STRUCTURE.md`
- **Title Case:** Track implementation docs
- **Descriptive names:** Clear, self-documenting

## 🔐 Security Files

### Secrets Management
- `.env.example` - Template (committed)
- `.env` - Actual secrets (gitignored)
- `scripts/generate-secrets.sh` - Secret generator

### Security Implementation
- `backend/app/middleware/` - Security middleware
- `backend/app/core/security.py` - Security utilities
- `docs/SECURITY_AUDIT.md` - Security assessment

## 🧪 Testing Structure

### Backend Tests
```
backend/tests/
├── conftest.py              # Test fixtures
├── test_api/
│   ├── test_dashboard.py    # Unit tests
│   └── test_jobs.py         # Integration tests
└── test_security.py         # Security tests
```

### Frontend Tests
```
frontend/src/tests/
├── setup.js                 # Test configuration
└── components/              # Component tests
```

## 📦 Dependencies

### Backend (Python)
- **Production:** `requirements.txt`
- **Development:** `requirements-dev.txt` (includes pytest, black, flake8)

### Frontend (JavaScript)
- **All dependencies:** `package.json`
- Includes dev dependencies for Vitest, ESLint

## 🚀 Deployment Files

### Development
- `docker-compose.yml`

### Production
- `docker-compose.yml` + `docker-compose.secure.yml`
- `.env` (from generate-secrets.sh)

### Backup/Restore
- `scripts/backup.sh`
- `scripts/restore.sh`

## ✨ Clean Structure Benefits

✅ **Organized** - Clear separation of concerns
✅ **Scalable** - Easy to add new features
✅ **Maintainable** - Logical file grouping
✅ **Documented** - README in each major directory
✅ **No Redundancy** - Legacy files removed
✅ **Production Ready** - Clean, professional structure

---

**Status:** ✅ Clean & Production Ready
**Version:** 1.0.0
**Last Cleanup:** 2025-01-15
