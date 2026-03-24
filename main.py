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

# ── AI CHAT PROXY ──────────────────────────────────────
from fastapi import Request
import urllib.request
import json
import os

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

@app.post("/ai/chat")
async def ai_chat(request: Request):
    body = await request.json()
    if not ANTHROPIC_API_KEY:
        return {"error": "ANTHROPIC_API_KEY not set"}
    try:
        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1000,
            "system": body.get("system", "You are an AI assistant for APPTS project tracking system."),
            "messages": body.get("messages", []),
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return {"content": result.get("content", [])}
    except urllib.error.HTTPError as e:
        return {"error": "API error: " + str(e.code)}
    except Exception as e:
        return {"error": str(e)}