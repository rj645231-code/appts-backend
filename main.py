from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models
from routes import users, projects, tasks, comments
from routes import google_auth

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="APPTS — Automated Project Progress Tracking System",
    version="3.0",
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
app.include_router(google_auth.router)

@app.get("/")
def home():
    return {"message": "APPTS API v3.0 running ✅"}
