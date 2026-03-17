# APPTS — Automated Project Progress Tracking System

## Stack
| Layer | Technology |
|---|---|
| Frontend | React (single-file HTML, or move to Vite+React) |
| Backend | Python FastAPI |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Auth | JWT (python-jose + passlib) |

---

## Folder Structure

```
appts/
├── backend/
│   ├── main.py           # FastAPI app entrypoint
│   ├── database.py       # SQLAlchemy engine & session
│   ├── models.py         # DB tables: User, Project, Task, TaskLog
│   ├── schemas.py        # Pydantic request/response models
│   ├── auth.py           # JWT create/verify, role guards
│   ├── assignment.py     # Auto-assignment engine (3 strategies)
│   ├── requirements.txt
│   └── routes/
│       ├── users.py      # Register, login, list
│       ├── projects.py   # CRUD + dashboard + workload analytics
│       └── tasks.py      # CRUD + auto-assign + audit log
└── frontend/
    └── dashboard.html    # Full React dashboard (single file)
```

---

## Quick Start

### 1 — Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2 — Run backend
```bash
uvicorn main:app --reload
# API: http://127.0.0.1:8000
# Docs: http://127.0.0.1:8000/docs
```
Database tables are created automatically on first run.

### 3 — Open dashboard
Open `frontend/dashboard.html` in a browser.
Make sure the `API` constant at the top of the file matches your backend URL.

---

## Switch to PostgreSQL

In `database.py`, set the env variable:
```bash
export DATABASE_URL="postgresql://user:password@localhost/appts_db"
```

---

## Key Features

### 🤖 Auto-Assignment (3 strategies)
When creating a task, leave `assigned_to` blank and pick a strategy:

| Strategy | How it works |
|---|---|
| `least_loaded` | Assigns to engineer with fewest active tasks |
| `round_robin` | Cycles through engineers in order |
| `role_match` | Matches task name keywords to engineer department |

### 👤 Role-Based Access
| Action | Engineer | Manager | Admin |
|---|---|---|---|
| Update own task progress | ✅ | ✅ | ✅ |
| Create/assign tasks | ❌ | ✅ | ✅ |
| Create projects | ❌ | ✅ | ✅ |
| Delete projects | ❌ | ❌ | ✅ |
| View all users | ✅ | ✅ | ✅ |

### 📝 Audit Log
Every status/progress change is saved to `task_logs` with:
- who changed it, when, old → new values, optional note

Retrieve via: `GET /tasks/{id}/logs`

### 📊 Analytics Endpoints
- `GET /projects/summary` — global KPIs
- `GET /projects/workload` — per-engineer breakdown
- `GET /projects/dashboard/{id}` — per-project stats
- `GET /tasks/delayed` — all overdue tasks

---

## API Quick Reference

```
POST   /users/register        Register new user
POST   /users/login           Get JWT token
GET    /users/me              Current user

POST   /projects/             Create project  (manager/admin)
GET    /projects/             List all projects
GET    /projects/summary      Overall KPIs
GET    /projects/workload     Engineer workload
GET    /projects/dashboard/{id}  Per-project stats
PATCH  /projects/{id}         Update project

POST   /tasks/?strategy=...   Create + auto-assign task
GET    /tasks/                List tasks (with filters)
GET    /tasks/my              My tasks (engineer)
GET    /tasks/delayed         Overdue tasks
PATCH  /tasks/{id}            Update task (progress/status)
GET    /tasks/{id}/logs       Audit history
DELETE /tasks/{id}            Delete task
```

---

## Roadmap (Next Steps)

1. **Email notifications** — FastAPI BackgroundTasks + SMTP (task assigned, deadline -24h)
2. **Gantt chart** — add start_date to tasks, render timeline in frontend
3. **Alembic migrations** — for safe schema changes in production
4. **AI delay prediction** — train on task history to flag at-risk tasks
5. **React + Vite** — split into proper component files
6. **Docker** — containerize backend + frontend
