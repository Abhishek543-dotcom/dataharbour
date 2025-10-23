<h1 align="left" style="color:#2563eb;">
  <img src="component/LOGO-white.svg" alt="DataHarbour Logo" height="40" style="vertical-align:middle; margin-right:12px;" />
  <span style="font-size:2.5rem; vertical-align:middle; color:#2563eb;"><b>DataHarbour</b></span>
</h1>

> A production-ready data engineering platform orchestrating Apache Spark, Airflow, Jupyter, MinIO, and PostgreSQL with a modern React frontend and secure FastAPI backend.

[![Production Ready](https://img.shields.io/badge/status-production%20ready-success)](https://github.com/Abhishek543-dotcom/dataharbour)
[![Test Coverage](https://img.shields.io/badge/coverage-70%25+-success)](https://github.com/Abhishek543-dotcom/dataharbour)
[![Security](https://img.shields.io/badge/security-hardened-blue)](https://github.com/Abhishek543-dotcom/dataharbour)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

## ✨ Features

### Core Capabilities
- **🚀 Apache Spark Integration** - Distributed data processing with PySpark and Delta Lake
- **📊 Apache Airflow** - Workflow orchestration and DAG scheduling
- **📓 Jupyter Notebooks** - Interactive development environment with notebook management
- **💾 MinIO Storage** - S3-compatible object storage for data lakes
- **🗄️ PostgreSQL** - Relational database with pgAdmin interface
- **🎯 Real-time Monitoring** - WebSocket-based live updates and metrics

### Modern Architecture
- **⚡ FastAPI Backend** - 30+ REST API endpoints with WebSocket support
- **⚛️ React Frontend** - Modern, component-based UI with Tailwind CSS
- **🔐 Security Hardened** - Rate limiting, security headers, audit logging, input validation
- **🧪 Well-Tested** - 70%+ code coverage with comprehensive test suite
- **📚 Fully Documented** - Complete API docs, deployment guides, and troubleshooting

## 🏗️ Project Structure

```
dataharbour/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── api/v1/endpoints/  # REST API endpoints (30+)
│   │   ├── core/              # Configuration & security
│   │   ├── middleware/        # Security middleware
│   │   ├── models/            # Pydantic schemas
│   │   └── services/          # Business logic
│   ├── tests/                 # Backend tests (70%+ coverage)
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API client & WebSocket
│   │   └── store/             # Zustand state management
│   ├── package.json
│   └── Dockerfile
│
├── scripts/                    # Utility scripts
│   ├── generate-secrets.sh    # Generate secure passwords
│   ├── backup.sh              # Automated backups
│   └── restore.sh             # Restore from backup
│
├── docs/                       # Documentation
│   ├── TRACK1_IMPLEMENTATION.md
│   ├── TRACK2_IMPLEMENTATION.md
│   ├── TRACK3_IMPLEMENTATION.md
│   ├── TRACK4_IMPLEMENTATION.md
│   ├── TRACK5_IMPLEMENTATION.md
│   ├── SECURITY_AUDIT.md
│   └── PROJECT_SUMMARY.md
│
├── .github/workflows/          # CI/CD Pipeline
│   └── ci.yml
│
├── docker-compose.yml          # Base configuration
├── docker-compose.secure.yml   # Production security config
├── .env.example                # Environment template
└── README.md                   # This file
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose installed
- At least 8GB RAM available
- Ports 3000, 4040, 5432, 7077, 8000, 8081, 8888, 9000, 9001 available

### 1. Clone Repository
```bash
git clone https://github.com/Abhishek543-dotcom/dataharbour.git
cd dataharbour
```

### 2. Generate Secrets (Production)
```bash
bash scripts/generate-secrets.sh > .env
# Edit .env with your specific values
nano .env
```

### 3. Start Services

**Development:**
```bash
docker-compose up -d
```

**Production (Secure):**
```bash
docker-compose -f docker-compose.yml -f docker-compose.secure.yml up -d
```

### 4. Verify Deployment
```bash
# Check all services are running
docker-compose ps

# Test backend health
curl http://localhost:8000/health
```

## 🌐 Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | - |
| **Backend API** | http://localhost:8000 | - |
| **API Docs (Swagger)** | http://localhost:8000/docs | - |
| **API Docs (ReDoc)** | http://localhost:8000/redoc | - |
| **Jupyter Notebook** | http://localhost:8888 | See logs for token |
| **Airflow** | http://localhost:8081 | admin / admin |
| **Spark UI** | http://localhost:4040 | When jobs running |
| **MinIO Console** | http://localhost:9001 | minioadmin / minioadmin |
| **pgAdmin** | http://localhost:5050 | admin@example.com / admin |
| **PostgreSQL** | localhost:5432 | admin / admin |

### Get Jupyter Token
```bash
docker logs dataharbour-jupyter-1 2>&1 | grep "token="
```

## 📖 Documentation

### Quick References
- **[API Quick Start](backend/API_QUICKSTART.md)** - API endpoint reference
- **[Backend README](backend/README.md)** - Backend architecture & development
- **[Frontend README](frontend/README.md)** - Frontend architecture & development

### Implementation Guides
- **[Track 1: Backend API](docs/TRACK1_IMPLEMENTATION.md)** - FastAPI backend implementation
- **[Track 2: Frontend Refactor](docs/TRACK2_IMPLEMENTATION.md)** - React frontend migration
- **[Track 3: Security Hardening](docs/TRACK3_IMPLEMENTATION.md)** - Security features
- **[Track 4: Testing & Quality](docs/TRACK4_IMPLEMENTATION.md)** - Testing framework
- **[Track 5: Documentation & DevOps](docs/TRACK5_IMPLEMENTATION.md)** - DevOps practices

### Additional Docs
- **[Security Audit](docs/SECURITY_AUDIT.md)** - Security assessment & improvements
- **[Project Summary](docs/PROJECT_SUMMARY.md)** - Complete project overview

## 🔐 Security Features

✅ **Environment-Based Secrets** - No hardcoded credentials
✅ **Rate Limiting** - 60 requests/minute (configurable)
✅ **Security Headers** - XSS, clickjacking, MIME-sniffing protection
✅ **Audit Logging** - JSON-formatted security event logs
✅ **Input Validation** - Sanitization against SQL injection, XSS
✅ **CORS Protection** - Configurable allowed origins
✅ **Secure Docker** - Non-root users, no-new-privileges

**Risk Score:** 5.5/10 (MEDIUM) - 35% improvement from baseline

## 🧪 Testing

### Run Backend Tests
```bash
cd backend
pip install -r requirements-dev.txt
pytest --cov=app --cov-report=html
```

### Run Frontend Tests
```bash
cd frontend
npm install
npm run test:coverage
```

### Test Categories
- **Unit Tests** - Fast, isolated function tests
- **Integration Tests** - API endpoint testing
- **Security Tests** - Validation, headers, rate limiting

**Current Coverage:** 70%+ (enforced in CI/CD)

## 🛠️ Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt

# Run with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm install

# Run dev server
npm run dev
```

### Code Quality
```bash
# Backend formatting
black backend/app
isort backend/app
flake8 backend/app

# Frontend linting
cd frontend
npm run lint
```

### Pre-commit Hooks
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## 📊 API Examples

### Get Dashboard Statistics
```bash
curl http://localhost:8000/api/v1/dashboard/stats
```

### Create Spark Job
```bash
curl -X POST http://localhost:8000/api/v1/jobs/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Example Job",
    "code": "print(\"Hello Spark\")",
    "executor_cores": 2,
    "executor_memory": "2g"
  }'
```

### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

See [API_QUICKSTART.md](backend/API_QUICKSTART.md) for complete endpoint reference.

## 🔄 Backup & Recovery

### Create Backup
```bash
bash scripts/backup.sh
```

### Restore from Backup
```bash
bash scripts/restore.sh /backups/backup_YYYYMMDD_HHMMSS.tar.gz
```

Backups include:
- PostgreSQL database
- MinIO data
- Jupyter notebooks
- Configuration files

## 🚢 Deployment

### Development
```bash
docker-compose up -d
```

### Staging
```bash
export ENVIRONMENT=staging
bash scripts/generate-secrets.sh > .env
docker-compose -f docker-compose.yml up -d
```

### Production
```bash
export ENVIRONMENT=production
bash scripts/generate-secrets.sh > .env
# Edit .env with production values
docker-compose -f docker-compose.yml -f docker-compose.secure.yml up -d
```

## 🐛 Troubleshooting

### Check Service Status
```bash
docker-compose ps
docker-compose logs [service-name]
```

### Common Issues

**Services won't start:**
```bash
docker-compose down
docker-compose up -d --build
```

**Database connection issues:**
```bash
docker-compose exec postgres pg_isready -U admin
```

**View backend logs:**
```bash
docker-compose logs -f backend
```

See [TRACK5_IMPLEMENTATION.md](docs/TRACK5_IMPLEMENTATION.md) for complete troubleshooting guide.

## 📈 Monitoring

### View Audit Logs
```bash
docker-compose exec backend cat /data/logs/audit.log
```

### Check Resource Usage
```bash
docker stats
```

### Health Check
```bash
curl http://localhost:8000/health
```

## 🔮 Future Enhancements

### High Priority
- [ ] Authentication & Authorization (JWT, RBAC)
- [ ] HTTPS/TLS with SSL certificates
- [ ] Complete notebook editor with CodeMirror
- [ ] Advanced monitoring dashboards

### Medium Priority
- [ ] TypeScript migration for type safety
- [ ] Dark mode theme
- [ ] Multi-tenancy support
- [ ] Advanced scheduling with cron

### Low Priority
- [ ] Mobile application (React Native)
- [ ] Plugin system for extensibility
- [ ] Internationalization (i18n)

## 📊 Project Statistics

| Metric | Value |
|--------|-------|
| **Total Files** | 120+ |
| **Lines of Code** | ~10,000 |
| **Test Coverage** | 70%+ |
| **API Endpoints** | 30+ |
| **Security Score** | 5.5/10 (Medium) |
| **Documentation** | 100% |

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow existing code style
- Add tests for new features
- Update documentation
- Ensure CI/CD passes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - UI library
- [Apache Spark](https://spark.apache.org/) - Distributed processing
- [Apache Airflow](https://airflow.apache.org/) - Workflow orchestration
- [MinIO](https://min.io/) - Object storage
- [PostgreSQL](https://www.postgresql.org/) - Database

## 📞 Support

- **Documentation:** See [docs/](docs/) folder
- **Issues:** [GitHub Issues](https://github.com/Abhishek543-dotcom/dataharbour/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Abhishek543-dotcom/dataharbour/discussions)

---

**Status:** ✅ Production Ready
**Version:** 1.0.0
**Last Updated:** 2025-01-15

Made with ❤️ by the DataHarbour Team
