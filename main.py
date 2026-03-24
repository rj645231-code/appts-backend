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

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

@app.post("/ai/chat")
async def ai_chat(request: Request):
    body = await request.json()
    if not GROQ_API_KEY:
        return {"error": "GROQ_API_KEY not configured on server"}
    try:
        # Build messages with system prompt
        messages = [{"role": "system", "content": body.get("system", "You are a helpful AI assistant.")}]
        messages += body.get("messages", [])

        payload = json.dumps({
            "model": "llama3-8b-8192",
            "messages": messages,
            "max_tokens": 1024,
            "temperature": 0.7,
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + GROQ_API_KEY,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            reply = result["choices"][0]["message"]["content"]
            return {"content": [{"type": "text", "text": reply}]}
    except urllib.error.HTTPError as e:
        body_err = e.read().decode()
        return {"error": "Groq API error " + str(e.code) + ": " + body_err}
    except Exception as e:
        return {"error": str(e)}