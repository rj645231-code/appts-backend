from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models
from routes import users, projects, tasks, comments
from routes import google_auth
import json
import os
import google.generativeai as genai

# ✅ Load API key safely
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ✅ Configure Gemini only if key exists
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ✅ Create DB tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="APPTS — Automated Project Progress Tracking System",
    version="3.0",
)

# ✅ CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Routers
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(comments.router)
app.include_router(google_auth.router)

@app.get("/")
def home():
    return {"message": "APPTS API v3.0 running"}


# ✅ AI Chat Route
@app.post("/ai/chat")
async def ai_chat(request: Request):
    if not GEMINI_API_KEY:
        return {"error": "GEMINI_API_KEY not configured on server"}

    try:
        body = await request.json()

        system_prompt = body.get(
            "system",
            "You are a helpful AI assistant for APPTS project tracking."
        )
        messages = body.get("messages", [])

        # ✅ Build prompt
        full_prompt = f"SYSTEM INSTRUCTIONS: {system_prompt}\n\n"

        for msg in messages:
            role = "User" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "")
            full_prompt += f"{role}: {content}\n"

        # ✅ Try multiple models (fallback system)
        model_names = [
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-pro"
        ]

        response = None
        last_error = None

        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)

                response = model.generate_content(
                    full_prompt,
                    generation_config={
                        "max_output_tokens": 1024,
                        "temperature": 0.7,
                    }
                )

                if response and getattr(response, "text", None):
                    break

            except Exception as e:
                last_error = str(e)
                continue

        # ❌ If all models fail
        if not response or not getattr(response, "text", None):
            return {
                "error": "All Gemini models failed",
                "details": last_error
            }

        # ✅ Success response
        return {
            "content": [
                {"type": "text", "text": response.text}
            ]
        }

    except Exception as e:
        return {"error": str(e)}