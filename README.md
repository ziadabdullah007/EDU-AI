# EduCore AI Platform

> **Production-Ready Multi-School Operations Backend**  
> Python 3.12 · FastAPI · SQLAlchemy 2.0 · PostgreSQL (Supabase) · Docker

---

## Overview

EduCore AI Platform is a **Modular Monolith** backend designed for private schools in Egypt and the Middle East. It provides a secure, scalable, and maintainable foundation for managing multiple schools from a single platform — with complete data isolation between each school.

The backend is architected to evolve into an AI-powered educational platform supporting RAG, LangGraph, MLflow, and vector databases — without requiring major refactoring.

---

## Architecture

```
HTTP Request
    ↓
Middleware (Logging, Security Headers, CORS)
    ↓
Router  ← validates request, delegates to service
    ↓
Service  ← all business logic lives here
    ↓
Repository  ← only database operations
    ↓
SQLAlchemy (AsyncSession)
    ↓
PostgreSQL (Supabase)
```

**Principles**: Clean Architecture · Repository Pattern · Service Layer · Dependency Injection · SOLID · DRY

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL via Supabase |
| Validation | Pydantic v2 |
| Auth | JWT (access + refresh tokens) |
| Hashing | bcrypt via passlib |
| Logging | structlog (JSON in production) |
| Migrations | Alembic |
| Testing | pytest + pytest-asyncio |
| Containers | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Deployment | Render |

---

## Modules

| Module | Description |
|---|---|
| **Authentication** | JWT registration, login, refresh, logout, RBAC |
| **Schools** | Multi-tenant school management |
| **Students** | Student profiles with school isolation |
| **Teachers** | Teacher profiles and class assignments |
| **Classes** | Classrooms with capacity enforcement |
| **Enrollment** | Student-class assignment with transfer history |
| **Attendance** | Daily attendance with bulk marking |
| **Grades** | Academic grade records with statistics |
| **Payments** | Financial records (immutable history) |
| **Documents** | Document metadata with external file storage |

---

## Roles & Permissions

| Role | Scope |
|---|---|
| `SUPER_ADMIN` | Full platform access across all schools |
| `SCHOOL_ADMIN` | Full access to their own school |
| `TEACHER` | Read access + attendance/grade management for assigned classes |
| `STUDENT` | Read-only access to own records |

---

## Project Structure

```
app/
├── api/v1/            # HTTP routers — no business logic
├── config/            # Settings and environment loading
├── core/              # Security (JWT + bcrypt) and logging
├── database/          # SQLAlchemy engine and session factory
├── dependencies/      # FastAPI Depends — repositories, services, auth guards
├── exceptions/        # Custom exception hierarchy + global handlers
├── middleware/        # Request logging, security headers
├── models/            # SQLAlchemy ORM models
├── repositories/      # Database access layer
├── schemas/           # Pydantic v2 request/response schemas
├── services/          # All business logic
├── utils/             # Pagination, response builders, validators
└── main.py            # Application factory + lifespan
tests/
alembic/
docker-compose.yml
Dockerfile
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL database (Supabase recommended)
- Docker (optional)

### 1. Clone & Configure

```bash
git clone https://github.com/your-org/educore-ai.git
cd educore-ai
cp .env.example .env
# Edit .env with your Supabase DATABASE_URL, JWT secrets, etc.
```

### 2. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run Locally

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Docker

```bash
# Copy and configure environment
cp .env.example .env

# Start the application
docker compose up --build

# Run in background
docker compose up -d
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | `postgresql+asyncpg://user:pass@host:5432/db` |
| `JWT_SECRET_KEY` | ✅ | Secret for signing access tokens |
| `JWT_REFRESH_SECRET_KEY` | ✅ | Secret for signing refresh tokens |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | | Default: 30 |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | | Default: 7 |
| `CORS_ORIGINS` | | Comma-separated origins |
| `APP_ENV` | | `development` / `staging` / `production` |
| `LOG_LEVEL` | | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `LOG_FORMAT` | | `json` (production) / `text` (development) |

---

## API Overview

All endpoints are versioned under `/api/v1/`.

### Authentication
```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
GET    /api/v1/auth/me
POST   /api/v1/auth/change-password
PATCH  /api/v1/auth/deactivate/{user_id}
```

### School-Scoped Resources
All resources below follow the pattern `/api/v1/schools/{school_id}/...`

```
# Schools
GET|POST        /api/v1/schools
GET|PATCH|DEL   /api/v1/schools/{school_id}

# Students
GET|POST        /api/v1/schools/{school_id}/students
GET|PATCH|DEL   /api/v1/schools/{school_id}/students/{student_id}

# Teachers, Classes, Enrollments, Attendance, Grades, Payments, Documents
# — follow the same REST pattern
```

### Pagination
Every list endpoint supports:
```
?page=1&page_size=20&search=john&sort_by=created_at&sort_order=desc
```

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

---

## Deployment (Render)

1. Connect your GitHub repository to Render.
2. Set all environment variables from `.env.example` in the Render dashboard.
3. Set the start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

---

## Future Roadmap

The architecture is already prepared for the following phases:

- **Phase 2**: Notifications, Email Service, File Upload Service
- **Phase 3**: AI Integration — RAG, LangGraph, OpenAI/Anthropic, Vector Databases
- **Phase 4**: Analytics Dashboard, MLflow, Predictive Attendance
- **Phase 5**: Mobile API optimizations, WebSockets, Background Workers
- **Phase 6**: Library, Transport, HR modules

---

## License

Private — EduCore AI Platform. All rights reserved.