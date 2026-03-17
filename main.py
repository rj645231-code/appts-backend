from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models
from routes import users, projects, tasks, comments

# Create all tables on startup (including new task_comments table)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="APPTS — Automated Project Progress Tracking System",
    version="2.1",
    description="Industry-grade project & task tracking with auto-assignment, comments, email alerts, and real-time analytics.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(comments.router)


@app.get("/", tags=["Health"])
def home():
    return {"message": "APPTS API v2.1 running ✅", "docs": "/docs"}
