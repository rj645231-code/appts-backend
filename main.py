from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models
from routes import users, projects, tasks, comments
from routes import google_auth
import urllib.request
import json
import os

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
    return {"message": "APPTS API v3.0 running"}

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

@app.post("/ai/chat")
async def ai_chat(request: Request):
    body = await request.json()
    if not GEMINI_API_KEY:
        return {"error": "GEMINI_API_KEY not configured on server"}
    try:
        system_prompt = body.get("system", "You are a helpful AI assistant for APPTS project tracking.")
        messages = body.get("messages", [])

        # Build Gemini contents - combine system + history
        contents = []
        # Add system as first user message
        contents.append({
            "role": "user",
            "parts": [{"text": "SYSTEM INSTRUCTIONS: " + system_prompt + "\n\nAcknowledge and wait for my question."}]
        })
        contents.append({
            "role": "model",
            "parts": [{"text": "Understood! I am your APPTS AI assistant. How can I help you?"}]
        })
        # Add conversation history
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        payload = json.dumps({
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": 1024,
                "temperature": 0.7,
            }
        }).encode("utf-8")

        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=" + GEMINI_API_KEY

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            reply = result["candidates"][0]["content"]["parts"][0]["text"]
            return {"content": [{"type": "text", "text": reply}]}
    except urllib.error.HTTPError as e:
        body_err = e.read().decode()
        return {"error": "Gemini API error " + str(e.code) + ": " + body_err}
    except Exception as e:
        return {"error": str(e)}